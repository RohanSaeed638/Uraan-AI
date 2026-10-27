from fastapi import HTTPException
from app.services.achievement_service import AchievementService
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.roadmap import AdaptRequest, RoadmapGenerateRequest
from app.repositories.roadmap_content_repository import (
    RoadmapContentRepository,
    summarize,
)
from app.services.roadmap_jobs import is_stale, revert_after_failure
from app.repositories.profile_repository import ProfileRepository
from app.repositories.roadmap_repository import RoadmapRepository
from app.models.enums import RoadmapStatus
from app.repositories.roadmap_task_repository import RoadmapTaskRepository
from app.schemas.roadmap import RoadmapActivateResponse
from app.services.gamification_service import (
    GamificationService,
    REASON_TASK,
    XP_TASK_COMPLETED,
)

class RoadmapService:

    def __init__(
        self,
        db: AsyncSession,
    ):

        self.db = db
        self.roadmap_task_repository = RoadmapTaskRepository(db)
        self.profile_repository = ProfileRepository(db)
        self.content = RoadmapContentRepository(db)

        self.roadmap_repository = RoadmapRepository(db)
        

    # ---- background jobs ----------------------------------------------------

    async def _profile(self, auth_user_id):
        profile = await self.profile_repository.get_by_auth_user_id(auth_user_id)

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        return profile

    async def _owned(self, roadmap_id, profile):
        roadmap = await self.content.load(roadmap_id)

        if roadmap is None or roadmap.profile_id != profile.id:
            raise HTTPException(status_code=404, detail="Roadmap not found")

        return roadmap

    def _settle_if_stale(self, roadmap) -> None:
        """A job that never reported back is given up on."""
        if is_stale(roadmap):
            revert_after_failure(roadmap, "generate" if not roadmap.status_before_job else "regenerate")

    async def start_generation(
        self,
        auth_user_id,
        data: RoadmapGenerateRequest,
    ):
        """Creates the roadmap row and returns at once; the caller starts the
        background job with the returned roadmap's id."""
        profile = await self._profile(auth_user_id)

        for running in await self.roadmap_repository.get_generating(profile.id):
            if is_stale(running):
                revert_after_failure(running, "generate")
            else:
                raise HTTPException(
                    status_code=409,
                    detail="Your roadmap is still being created.",
                )

        return await self.roadmap_repository.create_placeholder(profile, data)

    async def _begin_job(self, roadmap, kind: str) -> None:
        self._settle_if_stale(roadmap)

        if roadmap.status == RoadmapStatus.GENERATING:
            raise HTTPException(
                status_code=409,
                detail="This roadmap is already being updated.",
            )

        await self.content.save_version(roadmap, kind)
        roadmap.status_before_job = roadmap.status.value
        roadmap.status = RoadmapStatus.GENERATING
        roadmap.generation_error = None
        await self.db.commit()

    async def start_regenerate(self, roadmap_id, auth_user_id):
        profile = await self._profile(auth_user_id)
        roadmap = await self._owned(roadmap_id, profile)

        await self._begin_job(roadmap, "regenerate")

        return roadmap

    async def start_adapt(self, roadmap_id, auth_user_id, request: AdaptRequest):
        profile = await self._profile(auth_user_id)
        roadmap = await self._owned(roadmap_id, profile)

        if all(t.completed for p in roadmap.phases for t in p.tasks):
            raise HTTPException(
                status_code=409,
                detail="Everything in this roadmap is done: there is nothing left to adapt.",
            )

        await self._begin_job(roadmap, "adapt")

        return roadmap

    async def get_status(self, roadmap_id, auth_user_id):
        profile = await self._profile(auth_user_id)
        roadmap = await self._owned(roadmap_id, profile)

        if is_stale(roadmap):
            revert_after_failure(
                roadmap, "regenerate" if roadmap.status_before_job else "generate"
            )
            await self.db.commit()

        return {
            "id": roadmap.id,
            "title": roadmap.title,
            "status": roadmap.status,
            "error": roadmap.generation_error,
        }

    # ---- pause / resume -----------------------------------------------------

    async def pause(self, roadmap_id, auth_user_id):
        profile = await self._profile(auth_user_id)
        roadmap = await self._owned(roadmap_id, profile)

        if roadmap.status == RoadmapStatus.PAUSED:
            return roadmap

        if roadmap.status != RoadmapStatus.ACTIVE:
            raise HTTPException(
                status_code=409,
                detail="Only an active roadmap can be paused.",
            )

        roadmap.status = RoadmapStatus.PAUSED
        await self.db.commit()

        return roadmap

    async def resume(self, roadmap_id, auth_user_id):
        profile = await self._profile(auth_user_id)

        await self.roadmap_repository.lock_profile(profile_id=profile.id)
        roadmap = await self._owned(roadmap_id, profile)

        if roadmap.status == RoadmapStatus.ACTIVE:
            return roadmap

        if roadmap.status != RoadmapStatus.PAUSED:
            raise HTTPException(
                status_code=409,
                detail="Only a paused roadmap can be resumed.",
            )

        # Only one roadmap is active at a time.
        await self.roadmap_repository.archive_active_roadmaps(
            profile.id, except_id=roadmap.id
        )
        roadmap.status = RoadmapStatus.ACTIVE
        await self.db.commit()

        return roadmap

    # ---- versions -----------------------------------------------------------

    async def list_versions(self, roadmap_id, auth_user_id):
        profile = await self._profile(auth_user_id)
        roadmap = await self._owned(roadmap_id, profile)

        return [
            {
                "id": v.id,
                "version_number": v.version_number,
                "reason": v.reason,
                "created_at": v.created_at,
                **summarize(v.snapshot),
            }
            for v in await self.content.list_versions(roadmap.id)
        ]

    async def restore_version(self, roadmap_id, version_id, auth_user_id):
        profile = await self._profile(auth_user_id)
        roadmap = await self._owned(roadmap_id, profile)

        if roadmap.status == RoadmapStatus.GENERATING:
            raise HTTPException(
                status_code=409,
                detail="Wait for the roadmap to finish updating first.",
            )

        version = await self.content.get_version(roadmap.id, version_id)

        if version is None:
            raise HTTPException(status_code=404, detail="Version not found")

        # What is there now is saved first, so a restore can be undone.
        await self.content.save_version(roadmap, "restore")
        await self.content.replace_all(roadmap, version.snapshot)

        roadmap.title = version.snapshot.get("title") or roadmap.title
        roadmap.description = version.snapshot.get("description") or roadmap.description
        # Study time and duration belong to the plan, so they come back too.
        roadmap.daily_hours = version.snapshot.get("daily_hours") or roadmap.daily_hours
        roadmap.target_duration = (
            version.snapshot.get("target_duration") or roadmap.target_duration
        )
        roadmap.generation_error = None
        await self.db.commit()

        # Phases and tasks were just rewritten; read them back fresh. (Ids are
        # taken first: expiring the session also expires these objects.)
        roadmap_pk, profile_pk = roadmap.id, profile.id
        self.db.expire_all()

        return await self.roadmap_repository.get_by_id(roadmap_pk, profile_pk)

    async def get_current(
        self,
        auth_user_id,
    ):

        profile = await self.profile_repository.get_by_auth_user_id(
            auth_user_id
        )

        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        roadmap = await self.roadmap_repository.get_latest(
            profile.id
        )    
        return roadmap
    
    async def get_by_id(
        self,
        roadmap_id: UUID,
        user_id: UUID,
    ):

        roadmap = await self.roadmap_repository.get_by_id(
            roadmap_id=roadmap_id,
            user_id=user_id
        )

        if not roadmap:
            raise HTTPException(
                status_code=404,
                detail="Roadmap not found or does not belong to the user.",
            )

        return roadmap


    async def update_task_completion(
        self,
        task_id: UUID,
        completed: bool,
        auth_user_id: UUID,
    ):
        profile = await self.profile_repository.get_by_auth_user_id(
            auth_user_id
        )

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found",
            )

        task = await self.roadmap_task_repository.get_task_for_user(
            task_id=task_id,
            profile_id=profile.id,
        )

        if not task:
            raise HTTPException(
                status_code=404,
                detail="Task not found",
            )

        task.completed = completed

        await self.db.flush()

        if completed:
            await GamificationService(self.db).award(
                profile=profile,
                amount=XP_TASK_COMPLETED,
                reason=REASON_TASK,
                ref_id=task.id,
            )

        progress = await self.roadmap_task_repository.get_roadmap_progress(
            task.phase.roadmap_id,
        )

        if progress["total"] > 0:
            if progress["completed"] == progress["total"]:
                status = RoadmapStatus.COMPLETED
            else:
                status = RoadmapStatus.ACTIVE
  

            await self.roadmap_repository.update_status(
                task.phase.roadmap_id,
                status,
            )

            if status == RoadmapStatus.COMPLETED:
                await AchievementService(self.db).safe_evaluate(profile)
        await self.db.commit()
        await self.db.refresh(task)
        
        return task    

    async def get_all(
        self,
        auth_user_id: UUID,
    ):

        profile = await self.profile_repository.get_by_auth_user_id(
            auth_user_id
        )

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found",
            )

        roadmaps = await self.roadmap_repository.get_all_by_user(
            profile.id
        )

        summaries = []

        for roadmap in roadmaps:

            progress = await self.roadmap_task_repository.get_roadmap_progress(
                roadmap.id
            )

            percentage = 0

            if progress["total"] > 0:
                percentage = int(
                    progress["completed"]
                    * 100
                    / progress["total"]
                )

            summaries.append(
                {
                    "id": roadmap.id,
                    "title": roadmap.title,
                    "description": roadmap.description,
                    "status": roadmap.status,
                    "progress": percentage,
                    "completed_tasks": progress["completed"],
                    "total_tasks": progress["total"],
                    "updated_at": roadmap.updated_at,
                }
            )

        return summaries

    async def activate_roadmap(
        self,
        roadmap_id: UUID,
        auth_user_id: UUID,
    ) -> RoadmapActivateResponse:

        profile = await (
            self.profile_repository
            .get_by_auth_user_id(auth_user_id)
        )

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found",
            )

        try:
            # Prevent concurrent activation requests for this profile.
            await self.roadmap_repository.lock_profile(
                profile_id=profile.id,
            )

            # Validate ownership.
            roadmap = await (
                self.roadmap_repository
                .get_by_id_for_profile(
                    roadmap_id=roadmap_id,
                    profile_id=profile.id,
                )
            )

            if not roadmap:
                raise HTTPException(
                    status_code=404,
                    detail="Roadmap not found",
                )

            # Only archived and active roadmaps are eligible.
            if roadmap.status not in (
                RoadmapStatus.ARCHIVED,
                RoadmapStatus.ACTIVE,
            ):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Cannot activate a roadmap with "
                        f"status '{roadmap.status.value}'"
                    ),
                )

            # Idempotent: activating an already active roadmap
            # doesn't change its status.
            if roadmap.status == RoadmapStatus.ACTIVE:
                return RoadmapActivateResponse(
                    id=roadmap.id,
                    title=roadmap.title,
                    status=roadmap.status,
                    message="Roadmap is already active",
                )

            # Archive the previous active roadmap.
            await (
                self.roadmap_repository
                .archive_active_roadmaps(
                    profile_id=profile.id,
                )
            )

            # Activate the selected roadmap.
            roadmap.status = RoadmapStatus.ACTIVE

            await self.db.flush()
            await self.db.commit()
            await self.db.refresh(roadmap)

            return RoadmapActivateResponse(
                id=roadmap.id,
                title=roadmap.title,
                status=roadmap.status,
                message="Roadmap activated successfully",
            )

        except Exception:
            await self.db.rollback()
            raise

    async def delete_roadmap(
        self,
        roadmap_id: UUID,
        auth_user_id: UUID,
    ) -> None:

        profile = await (
            self.profile_repository
            .get_by_auth_user_id(auth_user_id)
        )

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found",
            )

        try:
            # Serialize roadmap-management operations.
            await self.roadmap_repository.lock_profile(
                profile_id=profile.id,
            )

            # Validate ownership.
            roadmap = await (
                self.roadmap_repository
                .get_by_id_for_profile(
                    roadmap_id=roadmap_id,
                    profile_id=profile.id,
                )
            )

            if not roadmap:
                raise HTTPException(
                    status_code=404,
                    detail="Roadmap not found",
                )

            # ORM/database cascades must cover dependent records.
            await self.roadmap_repository.delete_roadmap(
                roadmap
            )

            await self.db.commit()

        except Exception:
            await self.db.rollback()
            raise    