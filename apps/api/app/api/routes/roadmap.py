from uuid import UUID
from app.services.profile_service import ProfileService
from app.dependencies.services import get_roadmap_service
from app.dependencies.services import get_profile_service
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.api.dependencies import get_current_user

from app.schemas.roadmap import RoadmapResponse, UpdateTaskRequest, TaskResponse, RoadmapSummaryResponse

from app.services.roadmap_service import RoadmapService

router = APIRouter(
    prefix="/roadmaps",
    tags=["Roadmaps"],
)

@router.post(
    "/generate",
    response_model=RoadmapResponse,
)
async def generate_roadmap(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):

    service = RoadmapService(db)

    return await service.generate(
        current_user.id
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
    service: RoadmapService = Depends(get_roadmap_service),
):
    return await service.update_task_completion(
        task_id,
        payload.completed,
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