from sqlalchemy.ext.asyncio import AsyncSession

from app.models.roadmap_task import RoadmapTask


class RoadmapTaskRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        task: RoadmapTask,
    ):

        self.db.add(task)

        await self.db.flush()

        return task