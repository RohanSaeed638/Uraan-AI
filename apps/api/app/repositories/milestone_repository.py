from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.milestone import Milestone


class MilestoneRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        milestone: Milestone,
    ) -> Milestone:

        self.db.add(milestone)

        await self.db.commit()

        await self.db.refresh(milestone)

        return milestone

    async def get_by_phase(
        self,
        phase_id,
    ):

        result = await self.db.execute(
            select(Milestone).where(
                Milestone.phase_id == phase_id
            )
        )

        return result.scalars().all()