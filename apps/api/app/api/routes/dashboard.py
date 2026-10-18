from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard_service import (
    get_dashboard_summary,
)
from app.api.dependencies import get_current_user
from app.dependencies.services import get_roadmap_service, get_profile_service

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
)
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    roadmap_service=Depends(get_roadmap_service),
    profile_service=Depends(get_profile_service)
):
    user_id = current_user.id

    profile = await profile_service.get_profile(
        auth_user_id=user_id,
    )

    current_roadmap = await roadmap_service.get_current(
        auth_user_id=user_id,
    )

    return await get_dashboard_summary(
        db=db,
        user_id=user_id,
        user_name=(
            profile.full_name if profile else None
        ),
        career_goal=(
            profile.career_slug if profile else None
        ),
        current_roadmap=current_roadmap,
    )