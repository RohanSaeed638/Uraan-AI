from uuid import UUID
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.dependencies.services import get_roadmap_task_service
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