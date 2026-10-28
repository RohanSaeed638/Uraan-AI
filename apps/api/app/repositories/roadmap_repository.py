from uuid import UUID

from app.models.enums import RoadmapStatus
from app.schemas import roadmap
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.models.profile import Profile

class RoadmapRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_placeholder(self, profile, request) -> Roadmap:
        """An empty roadmap in the 'generating' state; a background job fills
        it in. Commits."""
        roadmap = Roadmap(
            profile_id=profile.id,
            title="Creating your roadmap",
            description="",
            status=RoadmapStatus.GENERATING,
            **self._request_fields(request),
        )

        self.db.add(roadmap)
        await self.db.commit()
        await self.db.refresh(roadmap)

        return roadmap

    async def get_generating(self, profile_id) -> list[Roadmap]:
        return list(
            (
                await self.db.execute(
                    select(Roadmap).where(
                        Roadmap.profile_id == profile_id,
                        Roadmap.status == RoadmapStatus.GENERATING,
                    )
                )
            ).scalars()
        )

    @staticmethod
    def _request_fields(request) -> dict:
        if request is None:
            return {}

        return {
            "career_slug": request.career_slug,
            "career_stage": request.career_stage,
            "skill_level": request.skill_level,
            "learning_goal": request.learning_goal,
            "learning_style": request.learning_style,
            "daily_hours": request.daily_hours,
            "target_duration": request.target_duration,
        }

    async def get_by_profile_id(
        self,
        profile_id: UUID,
    ) -> Roadmap | None:

        result = await self.db.execute(
            select(Roadmap).where(
                Roadmap.profile_id == profile_id
            ).order_by(
                    Roadmap.created_at.desc()
              )
        )

        return result.scalars().first()

    async def update(
        self,
        roadmap: Roadmap,
    ) -> Roadmap:

        await self.db.commit()

        await self.db.refresh(roadmap)

        return roadmap

    async def get_latest(
        self,
        profile_id,
    ):

        result = await self.db.execute(

            select(Roadmap)

            .options(

                selectinload(Roadmap.phases)

                .selectinload(RoadmapPhase.tasks)
                .selectinload(RoadmapTask.learning_units)
            )

            .where(
                Roadmap.profile_id == profile_id,
                # Roadmaps still being built, or that failed, are not
                # something to show as "current".
                Roadmap.status.notin_(
                    [RoadmapStatus.GENERATING, RoadmapStatus.FAILED]
                ),
            )

            .order_by(
                Roadmap.created_at.desc()
            )

        )

        return result.scalars().first()
    
    async def get_by_id(  
        self,
        roadmap_id: UUID,
        user_id: UUID,
    ):

        result = await self.db.execute(
            select(Roadmap)
            .options(
            selectinload(Roadmap.phases)
            .selectinload(RoadmapPhase.tasks)
            .selectinload(RoadmapTask.learning_units)
            )
            .where(
                Roadmap.id == roadmap_id,
                Roadmap.profile_id == user_id
            )
        )

        return result.scalar_one_or_none()

    async def update_status(
    self,
    roadmap_id: UUID,
    status: RoadmapStatus,
    ):
        result = await self.db.execute(
                select(Roadmap).where(
                Roadmap.id == roadmap_id
            )
        )

        roadmap = result.scalars().first()

        if not roadmap:
           return None

        # Ticking a task must not quietly change a roadmap that is archived,
        # paused or being rebuilt; only the explicit actions do that. Only
        # active and finished roadmaps move between active and completed.
        if status == RoadmapStatus.ACTIVE and roadmap.status not in (
            RoadmapStatus.ACTIVE,
            RoadmapStatus.COMPLETED,
        ):
            return roadmap

        if roadmap.status in (RoadmapStatus.GENERATING, RoadmapStatus.FAILED):
            return roadmap

        roadmap.status = status

        return roadmap

    async def get_all_by_user(
        self,
        user_id: UUID,
    ) -> list[Roadmap]:

        result = await self.db.execute(
            select(Roadmap)
            .where(Roadmap.profile_id == user_id)
            .order_by(Roadmap.updated_at.desc())
        )

        return result.scalars().all()        

    async def get_roadmap_for_progress(
        self,
        db: AsyncSession,
        roadmap_id: UUID,
        user_id: UUID,
    ) -> Roadmap | None:

        stmt = (
            select(Roadmap)
            .where(
                Roadmap.id == roadmap_id,
                Roadmap.user_id == user_id,
            )
            .options(
                selectinload(Roadmap.phases)
                .selectinload(RoadmapPhase.tasks)
                .selectinload(RoadmapTask.learning_units)
            )
        )

        result = await db.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_owned_roadmap(
        db: AsyncSession,
        user_id: UUID,
        roadmap_id: UUID,
    ):
        stmt = select(Roadmap).where(
            Roadmap.id == roadmap_id,
            Roadmap.user_id == user_id,
        )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def lock_profile(self, profile_id: UUID) -> None:
        stmt = (
            select(Profile.id)
            .where(Profile.id == profile_id)
            .with_for_update()
        )

        await self.db.execute(stmt)

    async def get_by_id_for_profile(
        self,
        roadmap_id: UUID,
        profile_id: UUID,
    ) -> Roadmap | None:

        stmt = (
            select(Roadmap)
            .where(
                Roadmap.id == roadmap_id,
                Roadmap.profile_id == profile_id,
            )
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()    

    async def archive_active_roadmaps(
        self,
        profile_id: UUID,
        except_id: UUID | None = None,
    ) -> None:

        conditions = [
            Roadmap.profile_id == profile_id,
            Roadmap.status == RoadmapStatus.ACTIVE,
        ]

        if except_id is not None:
            conditions.append(Roadmap.id != except_id)

        stmt = (
            update(Roadmap)
            .where(*conditions)
            .values(status=RoadmapStatus.ARCHIVED)
            .execution_options(synchronize_session="fetch")
        )

        await self.db.execute(stmt)

    async def get_active_for_profile(
        self,
        profile_id: UUID,
    ) -> Roadmap | None:

        stmt = (
            select(Roadmap)
            .where(
                Roadmap.profile_id == profile_id,
                Roadmap.status == RoadmapStatus.ACTIVE,
            )
            .order_by(Roadmap.created_at.desc())
            .limit(1)
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()    

    async def delete_roadmap(
        self,
        roadmap: Roadmap,
    ) -> None:
        await self.db.delete(roadmap)
        await self.db.flush()