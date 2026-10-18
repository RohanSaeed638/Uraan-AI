from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.base import get_db
from app.schemas.calendar import (
    CalendarScheduleResponse,
    CalendarSubscriptionResponse,
)
from app.services.calendar_service import CalendarService

router = APIRouter(
    prefix="/calendar",
    tags=["Calendar"],
)


@router.get("/schedule", response_model=CalendarScheduleResponse)
async def calendar_schedule(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await CalendarService(db).schedule(current_user.id)


@router.get("/subscription", response_model=CalendarSubscriptionResponse)
async def calendar_subscription(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    token = await CalendarService(db).token(current_user.id)

    return CalendarSubscriptionResponse(token=token)


@router.post(
    "/subscription/regenerate",
    response_model=CalendarSubscriptionResponse,
)
async def regenerate_calendar_subscription(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    token = await CalendarService(db).token(current_user.id, regenerate=True)

    return CalendarSubscriptionResponse(token=token)


@router.get("/feed/{token}.ics")
async def calendar_feed(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Public iCalendar feed; the unguessable token is the credential."""
    body = await CalendarService(db).feed(token)

    return Response(
        content=body,
        media_type="text/calendar; charset=utf-8",
        headers={"Cache-Control": "private, max-age=900"},
    )
