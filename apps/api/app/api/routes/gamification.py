from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.base import get_db
from app.repositories.profile_repository import ProfileRepository
from app.schemas.gamification import GamificationResponse
from app.services.gamification_service import GamificationService

router = APIRouter(
    prefix="/gamification",
    tags=["Gamification"],
)


@router.get("/me", response_model=GamificationResponse)
async def my_gamification(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    profile = await ProfileRepository(db).get_by_auth_user_id(
        current_user.id
    )

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return await GamificationService(db).summary(profile)
