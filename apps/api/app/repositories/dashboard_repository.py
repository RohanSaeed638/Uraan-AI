from uuid import UUID

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.models.task_learning_unit import TaskLearningUnit

async def get_dashboard_statistics(
    db: AsyncSession,
    user_id: UUID,
):
    roadmap_stmt = select(
        func.count(Roadmap.id),
        func.coalesce(
            func.sum(
                case(
                    (Roadmap.status == "completed", 1),
                    else_=0,
                )
            ),
            0,
        ),
    ).where(Roadmap.user_id == user_id)

    roadmap_result = (
        await db.execute(roadmap_stmt)
    ).one()

    task_stmt = (
        select(
            func.count(RoadmapTask.id),
            func.coalesce(
                func.sum(
                    case(
                        (RoadmapTask.completed.is_(True), 1),
                        else_=0,
                    )
                ),
                0,
            ),
        )
        .join(
            RoadmapPhase,
            RoadmapTask.phase_id == RoadmapPhase.id,
        )
        .join(
            Roadmap,
            RoadmapPhase.roadmap_id == Roadmap.id,
        )
        .where(Roadmap.user_id == user_id)
    )

    task_result = (
        await db.execute(task_stmt)
    ).one()

    unit_stmt = (
        select(
            func.count(TaskLearningUnit.id),
            func.coalesce(
                func.sum(
                    case(
                        (TaskLearningUnit.completed.is_(True), 1),
                        else_=0,
                    )
                ),
                0,
            ),
        )
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
        .where(Roadmap.user_id == user_id)
    )

    unit_result = (
        await db.execute(unit_stmt)
    ).one()

    return {
        "total_roadmaps": int(roadmap_result[0]),
        "completed_roadmaps": int(roadmap_result[1]),
        "total_tasks": int(task_result[0]),
        "completed_tasks": int(task_result[1]),
        "total_learning_units": int(unit_result[0]),
        "completed_learning_units": int(unit_result[1]),
    }