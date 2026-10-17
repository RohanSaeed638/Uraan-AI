from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.models.task_learning_unit import TaskLearningUnit


async def list_user_projects(
    db: AsyncSession,
    user_id: UUID,
    roadmap_id: UUID | None = None,
    completed: bool | None = None,
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
            TaskLearningUnit.type == "project",
        )
    )

    if roadmap_id is not None:
        stmt = stmt.where(
            Roadmap.id == roadmap_id
        )

    if completed is not None:
        stmt = stmt.where(
            TaskLearningUnit.completed.is_(completed)
        )

    stmt = stmt.order_by(
        Roadmap.created_at.desc(),
        RoadmapPhase.order.asc(),
        RoadmapTask.order.asc(),
        TaskLearningUnit.day.asc(),
        TaskLearningUnit.order.asc(),
    )

    result = await db.execute(stmt)

    return result.all()


async def get_user_project_by_id(
    db: AsyncSession,
    user_id: UUID,
    project_id: UUID,
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
            TaskLearningUnit.id == project_id,
            TaskLearningUnit.type == "project",
        )
    )

    result = await db.execute(stmt)

    return result.one_or_none()    