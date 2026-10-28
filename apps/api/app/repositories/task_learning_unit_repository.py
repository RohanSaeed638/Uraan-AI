from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.models.task_learning_unit import TaskLearningUnit


class TaskLearningUnitRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        learning_unit: TaskLearningUnit,
    ) -> TaskLearningUnit:

        self.db.add(learning_unit)

        await self.db.flush()

        return learning_unit

    async def create_many(
        self,
        learning_units: list[TaskLearningUnit],
    ) -> list[TaskLearningUnit]:

        self.db.add_all(learning_units)

        await self.db.flush()

        return learning_units

    async def get_by_task_id(
        self,
        task_id: UUID,
    ) -> list[TaskLearningUnit]:

        result = await self.db.execute(
            select(TaskLearningUnit)
            .where(
                TaskLearningUnit.task_id == task_id
            )
            .order_by(
                TaskLearningUnit.day,
                TaskLearningUnit.order,
            )
        )

        return list(result.scalars().all())

    async def get_by_id(
        self,
        learning_unit_id: UUID,
    ) -> TaskLearningUnit | None:

        result = await self.db.execute(
            select(TaskLearningUnit)
            .where(
                TaskLearningUnit.id == learning_unit_id
            )
        )

        return result.scalar_one_or_none()

    # async def get_by_id_for_user(
    #     self,
    #     learning_unit_id: UUID,
    #     profile_id: UUID,
    # ) -> TaskLearningUnit | None:

    #     result = await self.db.execute(
    #         select(TaskLearningUnit)
    #         .join(
    #             RoadmapTask,
    #             TaskLearningUnit.task_id == RoadmapTask.id,
    #         )
    #         .join(
    #             RoadmapPhase,
    #             RoadmapTask.phase_id == RoadmapPhase.id,
    #         )
    #         .join(
    #             Roadmap,
    #             RoadmapPhase.roadmap_id == Roadmap.id,
    #         )
    #         .where(
    #             TaskLearningUnit.id == learning_unit_id,
    #             Roadmap.profile_id == profile_id,
    #         )
    #     )

    #     return result.scalar_one_or_none()

    async def get_by_id_for_user(
        self,
        learning_unit_id: UUID,
        profile_id: UUID,
        for_update: bool = False,
    ) -> TaskLearningUnit | None:

        stmt = (
            select(TaskLearningUnit)
            .join(
                RoadmapTask,
                TaskLearningUnit.task_id == RoadmapTask.id,
            )
            .join(
                RoadmapPhase,
                RoadmapTask.phase_id == RoadmapPhase.id,
            )
            .join(
                Roadmap,
                RoadmapPhase.roadmap_id == Roadmap.id,
            )
            .where(
                TaskLearningUnit.id == learning_unit_id,
                Roadmap.profile_id == profile_id,
            )
        )

        if for_update:
            stmt = stmt.with_for_update(
                of=TaskLearningUnit
            )

            result = await self.db.execute(stmt)

        return result.scalar_one_or_none()
    
    async def get_by_task_for_user(
        self,
        task_id: UUID,
        profile_id: UUID,
    ) -> list[TaskLearningUnit]:

        result = await self.db.execute(
            select(TaskLearningUnit)
            .join(
                RoadmapTask,
                TaskLearningUnit.task_id == RoadmapTask.id,
            )
            .join(
                RoadmapPhase,
                RoadmapTask.phase_id == RoadmapPhase.id,
            )
            .join(
                Roadmap,
                RoadmapPhase.roadmap_id == Roadmap.id,
            )
            .where(
                TaskLearningUnit.task_id == task_id,
                Roadmap.profile_id == profile_id,
            )
            .order_by(
                TaskLearningUnit.day,
                TaskLearningUnit.order,
            )
        )

        return list(result.scalars().all())

    async def update_completion(
        self,
        learning_unit: TaskLearningUnit,
        completed: bool,
    ) -> TaskLearningUnit:

        learning_unit.completed = completed

        await self.db.flush()

        return learning_unit