from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.api.dependencies import get_current_user

from app.schemas.roadmap import RoadmapResponse

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