from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.base import get_db
from app.repositories.profile_repository import ProfileRepository
from app.schemas.achievement import AchievementsResponse, ReadinessResponse
from app.services.achievement_service import AchievementService
from app.services.readiness_service import ReadinessService

router = APIRouter(tags=["Achievements"])


async def _profile(db: AsyncSession, current_user):
    profile = await ProfileRepository(db).get_by_auth_user_id(current_user.id)

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return profile


@router.get("/achievements", response_model=AchievementsResponse)
async def my_achievements(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    profile = await _profile(db, current_user)

    # Unlocks anything earned since the last check, and may pick this month's
    # boss project, so it writes.
    result = await AchievementService(db).listing(profile)
    await db.commit()

    return result


@router.get("/readiness", response_model=ReadinessResponse)
async def my_readiness(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await ReadinessService(db).get(await _profile(db, current_user))
