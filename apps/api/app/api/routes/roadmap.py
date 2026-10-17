from uuid import UUID
from app.services.profile_service import ProfileService
from app.dependencies.services import get_roadmap_service, get_task_learning_unit_service
from app.dependencies.services import get_profile_service
from app.services.task_learning_unit_service import TaskLearningUnitService
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.api.dependencies import get_current_user
from app.schemas.roadmap import LearningUnitResponse, RoadmapResponse, UpdateTaskRequest, TaskResponse, RoadmapSummaryResponse, RoadmapGenerateRequest
from app.services.roadmap_service import RoadmapService
from app.schemas.progress import RoadmapProgressResponse
from app.services.progress_service import get_roadmap_progress
from app.schemas.roadmap import RoadmapActivateResponse

router = APIRouter(
    prefix="/roadmaps",
    tags=["Roadmaps"],
)

@router.post(
    "/generate",
    response_model=RoadmapResponse,
)
async def generate_roadmap(
    data: RoadmapGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):

    service = RoadmapService(db)

    return await service.generate(
        current_user.id,
        data=data,

    )

@router.get(
    "/current",
    response_model=RoadmapResponse,
)
async def get_current(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):

    service = RoadmapService(db)

    return await service.get_current(
        current_user.id
    )

@router.get(
    "/{roadmap_id}",
    response_model=RoadmapResponse,
)
async def get_roadmap(
    roadmap_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
):
    service = RoadmapService(db)
    profile = await profile_service.get_profile(
        auth_user_id=current_user.id)
    return await service.get_by_id(
        roadmap_id,
        profile.id
    )

@router.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
)
async def update_task(
    task_id: UUID,
    payload: UpdateTaskRequest,
    current_user=Depends(get_current_user),
    service: RoadmapService = Depends(get_roadmap_service),
):
    return await service.update_task_completion(
        task_id=task_id,
        completed=payload.completed,
        auth_user_id=current_user.id,
    )

@router.get(
    "",
    response_model=list[RoadmapSummaryResponse],
)
async def get_roadmaps(
    current_user=Depends(get_current_user),
    service: RoadmapService = Depends(
        get_roadmap_service
    ),
):
    return await service.get_all(
        current_user.id
    )

@router.get(
    "/tasks/{task_id}/learning-units",
    response_model=list[LearningUnitResponse],
)
async def get_task_learning_units(
    task_id: UUID,
    current_user=Depends(get_current_user),
    service: TaskLearningUnitService = Depends(
        get_task_learning_unit_service
    ),
):
    return await service.get_by_task(
        task_id,
        current_user.id,
    )


@router.get(
    "/{roadmap_id}/progress",
    response_model=RoadmapProgressResponse,
)
async def roadmap_progress(
    roadmap_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_roadmap_progress(
        db=db,
        roadmap_id=roadmap_id,
        user_id=current_user.id,
    )

@router.patch(
    "/{roadmap_id}/activate",
    response_model=RoadmapActivateResponse,
)
async def activate_roadmap(
    roadmap_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = RoadmapService(db)

    return await service.activate_roadmap(
        roadmap_id=roadmap_id,
        auth_user_id=current_user.id,
    )

@router.delete(
    "/{roadmap_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_roadmap(
    roadmap_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = RoadmapService(db)

    await service.delete_roadmap(
        roadmap_id=roadmap_id,
        auth_user_id=current_user.id,
    )