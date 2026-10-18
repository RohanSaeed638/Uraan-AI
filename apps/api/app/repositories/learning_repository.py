from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.models.task_learning_unit import TaskLearningUnit

async def get_next_learning_unit(
    db: AsyncSession,
    user_id: UUID,
):
    stmt = (
        select(
            Roadmap,
            RoadmapPhase,
            RoadmapTask,
            TaskLearningUnit,
        )
        .join(
            RoadmapPhase,
            RoadmapPhase.roadmap_id == Roadmap.id,
        )
        .join(
            RoadmapTask,
            RoadmapTask.phase_id == RoadmapPhase.id,
        )
        .join(
            TaskLearningUnit,
            TaskLearningUnit.task_id == RoadmapTask.id,
        )
        .where(
            Roadmap.user_id == user_id,
            Roadmap.status == "active",
            RoadmapTask.completed.is_(False),
            TaskLearningUnit.completed.is_(False),
        )
        .order_by(
            Roadmap.created_at.desc(),
            RoadmapPhase.order.asc(),
            RoadmapTask.order.asc(),
            TaskLearningUnit.day.asc(),
            TaskLearningUnit.order.asc(),
        )
        .limit(1)
    )

    result = await db.execute(stmt)

    return result.first()

async def get_roadmap_learning_units(
    db: AsyncSession,
    user_id: UUID,
    roadmap_id: UUID,
):
    stmt = (
        select(
            Roadmap,
            RoadmapPhase,
            RoadmapTask,
            TaskLearningUnit,
        )
        .join(
            RoadmapPhase,
            RoadmapPhase.roadmap_id == Roadmap.id,
        )
        .join(
            RoadmapTask,
            RoadmapTask.phase_id == RoadmapPhase.id,
        )
        .join(
            TaskLearningUnit,
            TaskLearningUnit.task_id == RoadmapTask.id,
        )
        .where(
            Roadmap.user_id == user_id,
            Roadmap.id == roadmap_id,
        )
        .order_by(
            RoadmapPhase.order.asc(),
            RoadmapTask.order.asc(),
            TaskLearningUnit.day.asc(),
            TaskLearningUnit.order.asc(),
        )
    )

    result = await db.execute(stmt)

    return result.all()