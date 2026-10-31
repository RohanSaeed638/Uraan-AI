"""The daily activity endpoint behind the heatmap."""
import asyncio
import selectors
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.base import get_db
from app.db.session import engine
from app.main import app
from app.models.profile import Profile
from app.models.xp_event import XPEvent


def run(coro):
    return asyncio.run(coro, loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))


def test_activity_is_grouped_by_day_and_empty_days_are_left_out():
    async def go():
        async with engine.connect() as conn:
            outer = await conn.begin()
            db = AsyncSession(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)
            uid = uuid4()
            await conn.execute(text("insert into auth.users (id, email) values (:i, :e)"), {"i": uid, "e": f"{uid}@x.test"})
            me = Profile(auth_user_id=uid, full_name="A", daily_hours=1, xp=0, streak_days=0, language="en")
            db.add(me)
            await db.flush()

            for amount in (10, 15):
                db.add(XPEvent(profile_id=me.id, amount=amount, reason="lesson", ref_id=uuid4()))

            await db.flush()

            async def get_db_override():
                yield db

            app.dependency_overrides[get_db] = get_db_override
            app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uid)
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
                    ok = await c.get("/api/v1/progress/activity?days=30")
                    bad = await c.get("/api/v1/progress/activity?days=2")
            finally:
                app.dependency_overrides.clear()
                await db.close()
                await outer.rollback()

            return ok, bad

    try:
        ok, bad = run(go())
    except OSError:
        pytest.skip("database not reachable")

    assert ok.status_code == 200
    days = ok.json()["days"]
    assert len(days) == 1 and days[0]["count"] == 2 and days[0]["xp"] == 25
    assert bad.status_code == 422
