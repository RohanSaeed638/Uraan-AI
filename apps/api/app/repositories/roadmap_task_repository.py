from uuid import UUID

from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap import Roadmap
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import func
from app.models.roadmap_task import RoadmapTask
from sqlalchemy import Integer
from sqlalchemy.orm import selectinload

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

    async def get_by_id(
    self,
        task_id: UUID,
    ) -> RoadmapTask | None:

        result = await self.db.execute(
            select(RoadmapTask)
            .options(
                selectinload(RoadmapTask.phase)
            )
            .where(RoadmapTask.id == task_id)
        )

        return result.scalar_one_or_none()

    async def update_task_completion(
        self,
        task_id: UUID,
        completed: bool,
    ) -> RoadmapTask | None:

        result = await self.db.execute(
            select(RoadmapTask)
            .options(
                selectinload(RoadmapTask.phase)
            )
            .where(
                RoadmapTask.id == task_id
            )
        )

        task = result.scalars().first()

        if not task:
            return None

        task.completed = completed

        await self.db.commit()
        await self.db.refresh(task)

        return task


    async def get_roadmap_progress(
        self,
        roadmap_id: UUID,
    ):
        result = await self.db.execute(
            select(
                func.count(RoadmapTask.id),
                func.sum(
                    RoadmapTask.completed.cast(Integer)
                )
            )
            .join(RoadmapPhase)
            .where(
                RoadmapPhase.roadmap_id == roadmap_id
            )
        )

        total, completed = result.one()

        return {
            "total": total or 0,
            "completed": completed or 0,
        }

    async def get_task_for_user(
        self,
        task_id: UUID,
        profile_id: UUID,
    ) -> RoadmapTask | None:

        result = await self.db.execute(
            select(RoadmapTask)
            .join(RoadmapPhase)
            .join(Roadmap)
            .options(
                selectinload(RoadmapTask.phase)
            )
            .where(
                RoadmapTask.id == task_id,
                Roadmap.profile_id == profile_id,
            )
        )

        return result.scalars().first()