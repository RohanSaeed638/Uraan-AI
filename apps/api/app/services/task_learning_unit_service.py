import logging
from app.ai.llm import use_profile
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.services.learning_unit_generator import LearningUnitGenerator
from app.core.career_catalog import is_coding_category
from app.services.lesson_writer import requeue_failed
from app.models.career import Career
from app.models.roadmap import Roadmap
from app.models.task_learning_unit import TaskLearningUnit
from app.repositories.profile_repository import ProfileRepository
from app.repositories.roadmap_task_repository import (
    RoadmapTaskRepository,
)
from app.repositories.task_learning_unit_repository import (
    TaskLearningUnitRepository,
)
from app.repositories.learning_activity_repository import (
    LearningActivityRepository,
)
from app.services.gamification_service import (
    GamificationService,
    REASON_LESSON,
    XP_LESSON_COMPLETED,
)

logger = logging.getLogger(__name__)


async def career_is_coding(db, slug: str | None) -> bool | None:
    """Whether this career's lessons get coding exercises, by its category in
    the database. None when it cannot be told (the catalogue file decides)."""
    try:
        category = (
            await db.execute(select(Career.category).where(Career.slug == slug))
        ).scalar_one_or_none()
    except Exception:
        return None

    return None if category is None else is_coding_category(category)


class TaskLearningUnitService:

    def __init__(
        self,
        db: AsyncSession,
    ):
        self.db = db

        self.learning_unit_repository = (
            TaskLearningUnitRepository(db)
        )

        self.profile_repository = ProfileRepository(db)

        self.learning_activity_repository = (
            LearningActivityRepository(db)
        )

        self.gamification = GamificationService(db)

        self.task_repository = RoadmapTaskRepository(db)

        self.generator = LearningUnitGenerator()

    async def ensure_plan(
        self,
        task_id: UUID,
        auth_user_id: UUID,
    ):
        """Returns the task with its lessons, writing them first if the
        task has none. Safe to call repeatedly or from two tabs at once:
        only one caller generates, the rest see the saved lessons."""
        profile = await self.profile_repository.get_by_auth_user_id(
            auth_user_id
        )

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found",
            )

        task = await self.task_repository.get_task_for_user(
            task_id=task_id,
            profile_id=profile.id,
        )

        if not task:
            raise HTTPException(
                status_code=404,
                detail="Task not found",
            )

        if task.learning_units:
            return task

        try:
            # One generator per task at a time. An advisory lock (released
            # on commit or rollback) avoids blocking edits to the task row.
            await self.db.execute(
                select(
                    func.pg_advisory_xact_lock(
                        func.hashtextextended(str(task.id), 0)
                    )
                )
            )

            # Another request may have finished while we waited.
            if await self.learning_unit_repository.get_by_task_id(task.id):
                await self.db.rollback()
                return await self.task_repository.get_task_for_user(
                    task_id=task_id,
                    profile_id=profile.id,
                    fresh=True,
                )

            roadmap = (
                await self.db.execute(
                    select(Roadmap).where(
                        Roadmap.id == task.phase.roadmap_id
                    )
                )
            ).scalar_one()

            try:
                use_profile(profile.id, profile.language)
                roadmap.coding_career = await career_is_coding(self.db, roadmap.career_slug)
                # Plan first (seconds); the lesson text is written behind it.
                units = await self.generator.generate_outline(roadmap, task, profile)
            except Exception as exc:
                logger.exception("Lesson generation failed for %s", task.id)
                raise HTTPException(
                    status_code=502,
                    detail=(
                        "Could not prepare the lessons right now. "
                        "Please try again."
                    ),
                ) from exc

            await self.learning_unit_repository.create_many(
                [
                    TaskLearningUnit(task_id=task.id, **unit)
                    for unit in units
                ]
            )

            await self.db.commit()

        except Exception:
            await self.db.rollback()
            raise

        return await self.task_repository.get_task_for_user(
            task_id=task_id,
            profile_id=profile.id,
            fresh=True,
        )

    async def requeue_failed(self, task_id: UUID, auth_user_id: UUID):
        """Puts the task's failed lessons back in the queue and returns the task."""
        profile = await self.profile_repository.get_by_auth_user_id(auth_user_id)

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        task = await self.task_repository.get_task_for_user(task_id=task_id, profile_id=profile.id)

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        await requeue_failed(self.db, task.id)
        await self.db.commit()

        return await self.task_repository.get_task_for_user(task_id=task_id, profile_id=profile.id, fresh=True)

    async def get_by_task(
        self,
        task_id: UUID,
        auth_user_id: UUID,
    ):
        profile = (
            await self.profile_repository
            .get_by_auth_user_id(auth_user_id)
        )

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found",
            )

        return await (
            self.learning_unit_repository
            .get_by_task_for_user(
                task_id,
                profile.id,
            )
        )

    async def get_by_id(
        self,
        learning_unit_id: UUID,
        auth_user_id: UUID,
    ):
        profile = (
            await self.profile_repository
            .get_by_auth_user_id(auth_user_id)
        )

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found",
            )

        learning_unit = await (
            self.learning_unit_repository
            .get_by_id_for_user(
                learning_unit_id,
                profile.id,
            )
        )

        if not learning_unit:
            raise HTTPException(
                status_code=404,
                detail="Learning unit not found",
            )

        return learning_unit

    async def update_completion(
        self,
        learning_unit_id: UUID,
        completed: bool,
        auth_user_id: UUID,
    ):
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
            learning_unit = await (
                self.learning_unit_repository
                .get_by_id_for_user(
                    learning_unit_id,
                    profile.id,
                    for_update=True,
                )
            )

            if not learning_unit:
                raise HTTPException(
                    status_code=404,
                    detail="Learning unit not found",
                )

            if getattr(learning_unit, "status", "ready") != "ready":
                raise HTTPException(
                    status_code=409,
                    detail="This lesson is still being written. Try again in a moment.",
                )

            was_completed = learning_unit.completed

            updated_unit = await (
                self.learning_unit_repository
                .update_completion(
                    learning_unit,
                    completed,
                )
            )

            # Record only the first completion.
            if completed and not was_completed:
                await (
                    self.learning_activity_repository
                    .create_completion_activity(
                        profile_id=profile.id,
                        learning_unit_id=learning_unit.id,
                        estimated_minutes=(
                            learning_unit.estimated_minutes or 0
                        ),
                    )
                )

                await self.gamification.award(
                    profile=profile,
                    amount=XP_LESSON_COMPLETED,
                    reason=REASON_LESSON,
                    ref_id=learning_unit.id,
                )

            await self.db.commit()
            await self.db.refresh(updated_unit)

            return updated_unit

        except Exception:
            await self.db.rollback()
            raise