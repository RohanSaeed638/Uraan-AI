from uuid import UUID

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.models.task_learning_unit import TaskLearningUnit

async def get_user_roadmap_statistics(
    db: AsyncSession,
    user_id: UUID,
):
    stmt = (
        select(
            Roadmap.id.label("roadmap_id"),
            Roadmap.title.label("title"),
            Roadmap.status.label("status"),
            func.count(RoadmapTask.id).label("total_tasks"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            RoadmapTask.completed.is_(True),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("completed_tasks"),
        )
        .outerjoin(
            RoadmapPhase,
            RoadmapPhase.roadmap_id == Roadmap.id,
        )
        .outerjoin(
            RoadmapTask,
            RoadmapTask.phase_id == RoadmapPhase.id,
        )
        .where(
            Roadmap.user_id == user_id,
            Roadmap.status != "archived",
        )
        .group_by(
            Roadmap.id,
            Roadmap.title,
            Roadmap.status,
        )
        .order_by(Roadmap.title.asc())
    )

    result = await db.execute(stmt)

    return result.all()


async def get_user_learning_statistics(
    db: AsyncSession,
    user_id: UUID,
):
    stmt = (
        select(
            func.count(TaskLearningUnit.id).label(
                "total_units"
            ),
            func.coalesce(
                func.sum(
                    case(
                        (
                            TaskLearningUnit.completed.is_(True),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("completed_units"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            TaskLearningUnit.completed.is_(True),
                            func.coalesce(
                                TaskLearningUnit.estimated_minutes,
                                0,
                            ),
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("completed_minutes"),
        )
        .select_from(TaskLearningUnit)
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
            Roadmap.user_id == user_id,
            Roadmap.status != "archived",
        )
    )

    result = await db.execute(stmt)

    return result.one()


async def get_user_phase_statistics(
    db: AsyncSession,
    user_id: UUID,
):
    stmt = (
        select(
            Roadmap.id.label("roadmap_id"),
            RoadmapPhase.id.label("phase_id"),
            RoadmapPhase.title.label("title"),
            RoadmapPhase.order.label("order"),
            func.count(RoadmapTask.id).label("total_tasks"),
            func.coalesce(
                func.sum(
                    case(
                        (RoadmapTask.completed.is_(True), 1),
                        else_=0,
                    )
                ),
                0,
            ).label("completed_tasks"),
        )
        .select_from(Roadmap)
        .join(RoadmapPhase, RoadmapPhase.roadmap_id == Roadmap.id)
        .outerjoin(RoadmapTask, RoadmapTask.phase_id == RoadmapPhase.id)
        .where(
            Roadmap.user_id == user_id,
            Roadmap.status != "archived",
        )
        .group_by(
            Roadmap.id,
            RoadmapPhase.id,
            RoadmapPhase.title,
            RoadmapPhase.order,
        )
        .order_by(RoadmapPhase.order.asc())
    )

    result = await db.execute(stmt)

    return result.all()