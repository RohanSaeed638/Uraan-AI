from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning_activity import LearningActivity


class LearningActivityRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_completion_activity(
        self,
        profile_id: UUID,
        learning_unit_id: UUID,
        estimated_minutes: int,
    ):
        stmt = (
            insert(LearningActivity)
            .values(
                profile_id=profile_id,
                learning_unit_id=learning_unit_id,
                activity_type="learning_unit_completed",
                estimated_minutes=estimated_minutes,
            )
            .on_conflict_do_nothing(
                constraint="uq_learning_activity_profile_unit"
            )
        )

        await self.db.execute(stmt)