from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.roadmap_phase import RoadmapPhase


class RoadmapPhaseRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        phase: RoadmapPhase,
    ) -> RoadmapPhase:

        self.db.add(phase)

        await self.db.commit()

        await self.db.refresh(phase)

        return phase

    async def get_by_roadmap(
        self,
        roadmap_id: UUID,
    ):

        result = await self.db.execute(
            select(RoadmapPhase).where(
                RoadmapPhase.roadmap_id == roadmap_id
            )
        )

        return result.scalars().all()