from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.dashboard_repository import (
    get_dashboard_statistics,
)
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    DashboardUserResponse,
    DashboardRoadmapResponse,
    DashboardNextLearningResponse,
    DashboardStatsResponse,
)

from app.services.progress_service import (
    get_roadmap_progress,
)
from app.services.learning_service import (
    get_continue_learning,
)


async def get_dashboard_summary(
    db: AsyncSession,
    user_id: UUID,
    user_name: str | None,
    career_goal: str | None,
    current_roadmap,
) -> DashboardSummaryResponse:

    statistics = await get_dashboard_statistics(
        db=db,
        user_id=user_id,
    )

    roadmap_response = None

    if current_roadmap is not None:
        progress = await get_roadmap_progress(
            db=db,
            roadmap_id=current_roadmap.id,
            user_id=user_id,
        )

        roadmap_response = DashboardRoadmapResponse(
            id=current_roadmap.id,
            title=current_roadmap.title,
            total_phases=progress.total_phases,
            total_tasks=progress.total_tasks,
            completed_tasks=progress.completed_tasks,
            completion_percentage=progress.completion_percentage,
        )

    next_unit = await get_continue_learning(
        db=db,
        user_id=user_id,
    )

    next_learning_response = None

    if next_unit is not None:
        next_learning_response = DashboardNextLearningResponse(
            roadmap_id=next_unit.roadmap_id,
            task_id=next_unit.task_id,
            learning_unit_id=next_unit.learning_unit_id,
            task_title=next_unit.task_title,
            learning_unit_title=next_unit.learning_unit_title,
            learning_unit_type=next_unit.learning_unit_type,
            estimated_minutes=next_unit.estimated_minutes,
        )

    return DashboardSummaryResponse(
        user=DashboardUserResponse(
            name=user_name,
            career_goal=career_goal,
        ),
        current_roadmap=roadmap_response,
        next_learning=next_learning_response,
        stats=DashboardStatsResponse(
            **statistics,
            remaining_tasks=(
                statistics["total_tasks"]
                - statistics["completed_tasks"]
            ),
        ),
    )