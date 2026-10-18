from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.base import get_db
from app.schemas.leaderboard import LeaderboardPeriod, LeaderboardResponse
from app.services.leaderboard_service import LeaderboardService

router = APIRouter(
    prefix="/leaderboard",
    tags=["Leaderboard"],
)


@router.get("", response_model=LeaderboardResponse)
async def leaderboard(
    period: LeaderboardPeriod = Query("weekly"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await LeaderboardService(db).get(
        period=period,
        auth_user_id=current_user.id,
    )
