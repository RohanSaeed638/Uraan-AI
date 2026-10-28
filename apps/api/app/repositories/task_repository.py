from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask

async def list_user_tasks(
    db: AsyncSession,
    user_id: UUID,
    roadmap_id: UUID | None = None,
    completed: bool | None = None,
) -> list[RoadmapTask]:

    stmt = (
        select(RoadmapTask)
        .join(
            RoadmapPhase,
            RoadmapTask.phase_id == RoadmapPhase.id,
        )
        .join(
            Roadmap,
            RoadmapPhase.roadmap_id == Roadmap.id,
        )
        .where(Roadmap.user_id == user_id)
        .options(selectinload(RoadmapTask.phase))
        .order_by(
            RoadmapPhase.order.asc(),
            RoadmapTask.order.asc(),
        )
    )

    if roadmap_id is not None:
        stmt = stmt.where(Roadmap.id == roadmap_id)

    if completed is not None:
        stmt = stmt.where(RoadmapTask.completed == completed)

    result = await db.execute(stmt)

    return list(result.scalars().all())