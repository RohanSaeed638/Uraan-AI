"""Unsubscribe links in emails. Public on purpose: the link is signed, so it
works without signing in (and for mail apps that call it themselves)."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email_token import read_token
from app.db.base import get_db
from app.models.user_settings import UserSettings

router = APIRouter(tags=["Email"])

INVALID = "This unsubscribe link is not valid."


class UnsubscribeState(BaseModel):
    subscribed: bool


async def _settings_for(db: AsyncSession, token: str) -> UserSettings:
    profile_id = read_token(token)

    if profile_id is None:
        raise HTTPException(status_code=400, detail=INVALID)

    row = (
        await db.execute(select(UserSettings).where(UserSettings.profile_id == profile_id))
    ).scalar_one_or_none()

    if row is None:
        raise HTTPException(status_code=400, detail=INVALID)

    return row


@router.get("/email/unsubscribe", response_model=UnsubscribeState)
async def unsubscribe_state(token: str = Query(min_length=10, max_length=300), db: AsyncSession = Depends(get_db)):
    """Whether the person behind the link still gets email."""
    row = await _settings_for(db, token)

    return UnsubscribeState(subscribed=bool(row.email_notifications))


@router.post("/email/unsubscribe", response_model=UnsubscribeState)
async def unsubscribe(token: str = Query(min_length=10, max_length=300), db: AsyncSession = Depends(get_db)):
    """Turns email notifications off. Safe to repeat. In-app and push
    notifications are not affected."""
    row = await _settings_for(db, token)
    row.email_notifications = False
    await db.commit()

    return UnsubscribeState(subscribed=False)
