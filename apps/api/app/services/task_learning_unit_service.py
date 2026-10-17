from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.profile_repository import ProfileRepository
from app.repositories.task_learning_unit_repository import (
    TaskLearningUnitRepository,
)
from app.repositories.learning_activity_repository import (
    LearningActivityRepository,
)


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

            await self.db.commit()
            await self.db.refresh(updated_unit)

            return updated_unit

        except Exception:
            await self.db.rollback()
            raise