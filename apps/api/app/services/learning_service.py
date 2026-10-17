from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.learning_repository import (
    get_next_learning_unit,
    get_roadmap_learning_units,
)
from app.schemas.learning import ContinueLearningResponse

from collections import defaultdict
from typing import Literal
from uuid import UUID

from fastapi import HTTPException, Depends

from app.schemas.learning import (
    LearningAgendaResponse,
    LearningAgendaDayResponse,
    LearningAgendaUnitResponse,
)

from app.repositories.roadmap_repository import RoadmapRepository

async def get_continue_learning(
    db: AsyncSession,
    user_id: UUID,
) -> ContinueLearningResponse | None:

    result = await get_next_learning_unit(
        db=db,
        user_id=user_id,
    )

    if result is None:
        return None

    roadmap, phase, task, unit = result

    return ContinueLearningResponse(
        roadmap_id=roadmap.id,
        roadmap_title=roadmap.title,
        phase_id=phase.id,
        phase_title=phase.title,
        task_id=task.id,
        task_title=task.title,
        learning_unit_id=unit.id,
        learning_unit_title=unit.title,
        learning_unit_type=unit.type,
        day=unit.day,
        estimated_minutes=unit.estimated_minutes,
    )


LearningView = Literal["today", "week", "all"]

async def get_learning_agenda(
    db: AsyncSession,
    user_id: UUID,
    roadmap_id: UUID,
    view: LearningView = "today",
    roadmap_repository: RoadmapRepository = Depends(RoadmapRepository),
) -> LearningAgendaResponse:

    rows = await get_roadmap_learning_units(
        db=db,
        user_id=user_id,
        roadmap_id=roadmap_id,
    )

    roadmap = await roadmap_repository.get_owned_roadmap(
        db=db,
        user_id=user_id,
        roadmap_id=roadmap_id,
    )

    if roadmap is None:
        raise HTTPException(
            status_code=404,
            detail="Roadmap not found",
        )

    grouped = defaultdict(list)

    roadmap_title = None
    current_group_index = 0
    last_task_day = None

    for roadmap, phase, task, unit in rows:
        roadmap_title = roadmap.title

        task_day_key = (task.id, unit.day)

        if task_day_key != last_task_day:
            current_group_index += 1
            last_task_day = task_day_key

        grouped[current_group_index].append(
            LearningAgendaUnitResponse(
                id=unit.id,
                roadmap_id=roadmap.id,
                task_id=task.id,
                task_title=task.title,
                title=unit.title,
                type=(
                    unit.type.value
                    if hasattr(unit.type, "value")
                    else unit.type
                ),
                order=unit.order,
                estimated_minutes=unit.estimated_minutes,
                completed=unit.completed,
            )
        )

    all_days = [
        LearningAgendaDayResponse(
            day=day,
            units=units,
            total_estimated_minutes=sum(
                unit.estimated_minutes or 0
                for unit in units
            ),
        )
        for day, units in grouped.items()
    ]

    first_incomplete_index = next(
        (
            index
            for index, day in enumerate(all_days)
            if any(not unit.completed for unit in day.units)
        ),
        len(all_days),
    )

    if view == "today":
        selected_days = all_days[
            first_incomplete_index:first_incomplete_index + 1
        ]
    elif view == "week":
        selected_days = all_days[
            first_incomplete_index:first_incomplete_index + 7
        ]
    else:
        selected_days = all_days

    return LearningAgendaResponse(
        roadmap_id=roadmap_id,
        roadmap_title=roadmap_title,
        view=view,
        total_units=sum(len(day.units) for day in selected_days),
        completed_units=sum(
            unit.completed
            for day in selected_days
            for unit in day.units
        ),
        total_estimated_minutes=sum(
            day.total_estimated_minutes
            for day in selected_days
        ),
        days=selected_days,
    )