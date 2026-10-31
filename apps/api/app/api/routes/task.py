from uuid import UUID
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.dependencies.services import (
    get_roadmap_task_service,
    get_task_learning_unit_service,
)
from app.services.lesson_writer import needs_writer, write_pending_lessons
from app.services.task_learning_unit_service import (
    TaskLearningUnitService,
)
from app.schemas.task import (
    RoadmapTaskResponse,
    UpdateTaskCompletionRequest,
)
from app.services.roadmap_task_service import RoadmapTaskService

from app.db.base import get_db
from app.schemas.task import TaskListItemResponse
from app.services.task_service import get_user_tasks

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


@router.get(
    "/{task_id}",
    response_model=RoadmapTaskResponse,
)
async def get_task(
    task_id: UUID,
    current_user=Depends(get_current_user),
    service: RoadmapTaskService = Depends(
        get_roadmap_task_service
    ),
):
    return await service.get_task(
        task_id=task_id,
        auth_user_id=current_user.id,
    )


@router.post(
    "/{task_id}/learning-plan",
    response_model=RoadmapTaskResponse,
)
async def create_learning_plan(
    task_id: UUID,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    service: TaskLearningUnitService = Depends(
        get_task_learning_unit_service
    ),
):
    """Plans the task's lessons if it has none (a few seconds), then returns
    the task. The lesson text is written in the background, first day first:
    each lesson's `status` says whether it is ready. Calling this again returns
    what is saved and restarts any writing that was interrupted."""
    task = await service.ensure_plan(
        task_id=task_id,
        auth_user_id=current_user.id,
    )

    if needs_writer(task.learning_units):
        background_tasks.add_task(write_pending_lessons, task.id)

    return task


@router.post(
    "/{task_id}/learning-plan/retry",
    response_model=RoadmapTaskResponse,
)
async def retry_lessons(
    task_id: UUID,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    service: TaskLearningUnitService = Depends(
        get_task_learning_unit_service
    ),
):
    """Writes the lessons that failed again."""
    task = await service.requeue_failed(task_id=task_id, auth_user_id=current_user.id)
    background_tasks.add_task(write_pending_lessons, task.id)

    return task


@router.patch(
    "/{task_id}",
    response_model=RoadmapTaskResponse,
)
async def update_task_completion(
    task_id: UUID,
    payload: UpdateTaskCompletionRequest,
    current_user=Depends(get_current_user),
    service: RoadmapTaskService = Depends(
        get_roadmap_task_service
    ),
):
    return await service.update_completion(
        task_id=task_id,
        completed=payload.completed,
        auth_user_id=current_user.id,
    )

@router.get("", response_model=list[TaskListItemResponse])
async def list_tasks(
    roadmap_id: UUID | None = Query(default=None),
    status: Literal["todo", "completed"] | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_user_tasks(
        db=db,
        user_id=current_user.id,
        roadmap_id=roadmap_id,
        status=status,
    )