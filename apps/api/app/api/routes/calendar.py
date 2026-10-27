from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.base import get_db
from app.schemas.calendar import (
    CalendarScheduleResponse,
    CalendarSubscriptionResponse,
    MoveRequest,
    OptimiseRequest,
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


@router.put("/units/{unit_id}/date", response_model=CalendarScheduleResponse)
async def move_unit(
    unit_id: UUID,
    payload: MoveRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Moves a lesson to a day. It stays there until it is unpinned."""
    return await CalendarService(db).move(current_user.id, unit_id, payload.date)


@router.delete("/units/{unit_id}/date", response_model=CalendarScheduleResponse)
async def unpin_unit(
    unit_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Lets the planner place the lesson again."""
    return await CalendarService(db).unpin(current_user.id, unit_id)


@router.post("/optimise", response_model=CalendarScheduleResponse)
async def optimise_schedule(
    payload: OptimiseRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Turns "exams next week, evenings only" into planner rules."""
    return await CalendarService(db).optimise(current_user.id, payload.request)


@router.delete("/preferences", response_model=CalendarScheduleResponse)
async def reset_schedule_preferences(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await CalendarService(db).reset_preferences(current_user.id)


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
