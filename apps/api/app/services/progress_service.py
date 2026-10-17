from uuid import UUID

from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.roadmap_repository import RoadmapRepository
from app.schemas.progress import (
    PhaseProgressResponse,
    RoadmapProgressResponse,
    RoadmapCountStats,
    CompletionStats,
    RoadmapProgressItem,
    ProgressOverviewResponse,
)

from app.repositories.progress_repository import (
    get_user_roadmap_statistics,
    get_user_learning_statistics,
)

def calculate_percentage(completed: int, total: int) -> float:
    if total == 0:
        return 0.0

    return round((completed / total) * 100, 2)


async def get_roadmap_progress(
    db: AsyncSession,
    roadmap_id: UUID,
    user_id: UUID,
    roadmap_repository: RoadmapRepository = Depends(RoadmapRepository),
) -> RoadmapProgressResponse:

    roadmap = await roadmap_repository.get_roadmap_for_progress(
        db=db,
        roadmap_id=roadmap_id,
        user_id=user_id,
    )

    if roadmap is None:
        raise HTTPException(
            status_code=404,
            detail="Roadmap not found",
        )

    total_tasks = 0
    completed_tasks = 0

    total_learning_units = 0
    completed_learning_units = 0

    phase_progress = []

    for phase in sorted(
        roadmap.phases,
        key=lambda phase: phase.order,
    ):
        phase_total = len(phase.tasks)

        phase_completed = sum(
            1 for task in phase.tasks if task.completed
        )

        total_tasks += phase_total
        completed_tasks += phase_completed

        for task in phase.tasks:
            units = task.learning_units

            total_learning_units += len(units)

            completed_learning_units += sum(
                1 for unit in units if unit.completed
            )

        phase_progress.append(
            PhaseProgressResponse(
                phase_id=phase.id,
                title=phase.title,
                total_tasks=phase_total,
                completed_tasks=phase_completed,
                completion_percentage=calculate_percentage(
                    phase_completed,
                    phase_total,
                ),
            )
        )

    return RoadmapProgressResponse(
        roadmap_id=roadmap.id,
        total_phases=len(roadmap.phases),
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        remaining_tasks=total_tasks - completed_tasks,
        completion_percentage=calculate_percentage(
            completed_tasks,
            total_tasks,
        ),
        total_learning_units=total_learning_units,
        completed_learning_units=completed_learning_units,
        learning_completion_percentage=calculate_percentage(
            completed_learning_units,
            total_learning_units,
        ),
        phases=phase_progress,
    )


def calculate_completion(
    completed: int,
    total: int,
) -> float:
    if total == 0:
        return 0.0

    return round((completed / total) * 100, 2)


async def get_progress_overview(
    db: AsyncSession,
    user_id: UUID,
) -> ProgressOverviewResponse:

    roadmap_rows = await get_user_roadmap_statistics(
        db=db,
        user_id=user_id,
    )

    learning_stats = await get_user_learning_statistics(
        db=db,
        user_id=user_id,
    )

    total_roadmaps = len(roadmap_rows)

    completed_roadmaps = 0
    in_progress_roadmaps = 0

    total_tasks = 0
    completed_tasks = 0

    roadmap_progress = []

    for row in roadmap_rows:
        status = (
            row.status.value
            if hasattr(row.status, "value")
            else row.status
        )

        if status == "completed":
            completed_roadmaps += 1

        elif status == "in_progress":
            in_progress_roadmaps += 1

        total_tasks += row.total_tasks
        completed_tasks += row.completed_tasks

        roadmap_progress.append(
            RoadmapProgressItem(
                roadmap_id=row.roadmap_id,
                title=row.title,
                total_tasks=row.total_tasks,
                completed_tasks=row.completed_tasks,
                completion_percentage=calculate_completion(
                    row.completed_tasks,
                    row.total_tasks,
                ),
            )
        )

    total_units = int(learning_stats.total_units)
    completed_units = int(
        learning_stats.completed_units
    )

    completed_minutes = int(
        learning_stats.completed_minutes
    )

    return ProgressOverviewResponse(
        roadmaps=RoadmapCountStats(
            total=total_roadmaps,
            completed=completed_roadmaps,
            in_progress=in_progress_roadmaps,
        ),
        tasks=CompletionStats(
            total=total_tasks,
            completed=completed_tasks,
            remaining=total_tasks - completed_tasks,
            completion_percentage=calculate_completion(
                completed_tasks,
                total_tasks,
            ),
        ),
        learning_units=CompletionStats(
            total=total_units,
            completed=completed_units,
            remaining=total_units - completed_units,
            completion_percentage=calculate_completion(
                completed_units,
                total_units,
            ),
        ),
        estimated_completed_learning_hours=round(
            completed_minutes / 60,
            2,
        ),
        roadmap_progress=roadmap_progress,
    )