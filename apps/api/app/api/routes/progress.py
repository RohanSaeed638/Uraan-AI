from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.models.profile import Profile
from app.models.xp_event import XPEvent
from app.api.dependencies import get_current_user

from app.schemas.progress import (
    ProgressOverviewResponse,
)

from app.services.progress_service import (
    get_progress_overview,
)

router = APIRouter(
    prefix="/progress",
    tags=["Progress"],
)


@router.get(
    "/overview",
    response_model=ProgressOverviewResponse,
)
async def progress_overview(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_progress_overview(
        db=db,
        user_id=current_user.id,
    )


@router.get("/activity")
async def progress_activity(
    days: int = Query(default=120, ge=7, le=366),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Learning done per day (XP awards and how many), for the heatmap and chart.
    Days with nothing are left out."""
    profile_id = (
        await db.execute(select(Profile.id).where(Profile.auth_user_id == current_user.id))
    ).scalar_one_or_none()

    if profile_id is None:
        return {"days": []}

    since = datetime.now(timezone.utc) - timedelta(days=days)
    day = func.date(func.timezone("UTC", XPEvent.created_at))
    rows = (
        await db.execute(
            select(day, func.count(), func.coalesce(func.sum(XPEvent.amount), 0))
            .where(XPEvent.profile_id == profile_id, XPEvent.created_at >= since)
            .group_by(day)
            .order_by(day)
        )
    ).all()

    return {"days": [{"date": d.isoformat(), "count": c, "xp": int(x)} for d, c, x in rows]}
