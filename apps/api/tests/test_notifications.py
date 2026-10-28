"""The notification list (paging, unread only) and the streak milestone."""
import asyncio
import selectors
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.models.notification import Notification
from app.models.profile import Profile
from app.repositories.notification_repository import NotificationRepository
from app.services.achievement_service import STREAK_MILESTONES, AchievementService
from app.services.notification_service import NotificationService


def with_db(fn, **profile_fields):
    async def go():
        engine = create_async_engine(settings.DATABASE_URL)
        try:
            async with engine.connect() as conn:
                trans = await conn.begin()
                db = AsyncSession(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)
                try:
                    me = Profile(
                        auth_user_id=uuid4(), full_name="Ayesha", daily_hours=1, xp=0,
                        streak_days=0, **profile_fields,
                    )
                    db.add(me)
                    await db.flush()

                    return await fn(db, me)
                finally:
                    await db.close()
                    await trans.rollback()
        finally:
            await engine.dispose()

    try:
        return asyncio.run(go(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))
    except OSError as exc:
        pytest.skip(f"database not reachable: {type(exc).__name__}")


async def add(db, me, count, read_every=0):
    now = datetime.now(timezone.utc)

    for i in range(count):
        db.add(
            Notification(
                profile_id=me.id, type="daily_reminder", title=f"n{i}", body="b", url="/x",
                dedupe_key=f"k{i}", created_at=now - timedelta(minutes=i),
                read_at=now if read_every and i % read_every == 0 else None,
            )
        )

    await db.flush()


def service(db, me):
    s = NotificationService(db)

    async def profile(_):
        return me

    s._profile = profile

    return s


def test_the_list_pages_newest_first_and_says_when_there_is_more():
    async def check(db, me):
        await add(db, me, 7)
        s = service(db, me)

        first = await s.list(me.auth_user_id, limit=3)
        second = await s.list(me.auth_user_id, limit=3, before=first.notifications[-1].created_at)
        last = await s.list(me.auth_user_id, limit=3, before=second.notifications[-1].created_at)

        titles = [[n.title for n in page.notifications] for page in (first, second, last)]

        assert titles == [["n0", "n1", "n2"], ["n3", "n4", "n5"], ["n6"]]
        assert (first.has_more, second.has_more, last.has_more) == (True, True, False)
        assert first.unread_count == 7

    with_db(check)


def test_unread_only():
    async def check(db, me):
        await add(db, me, 6, read_every=2)  # n0, n2, n4 are read
        everything = await service(db, me).list(me.auth_user_id)
        unread = await service(db, me).list(me.auth_user_id, unread_only=True)

        assert len(everything.notifications) == 6
        assert [n.title for n in unread.notifications] == ["n1", "n3", "n5"]
        assert unread.unread_count == 3

    with_db(check)


def test_someone_elses_notifications_are_not_listed():
    async def check(db, me):
        other = Profile(auth_user_id=uuid4(), full_name="Other", daily_hours=1)
        db.add(other)
        await db.flush()
        await add(db, other, 3)

        assert (await service(db, me).list(me.auth_user_id)).notifications == []

    with_db(check)


async def streak_notes(db, me):
    return list(
        (await db.execute(select(Notification.title).where(Notification.profile_id == me.id, Notification.type == "streak"))).scalars()
    )


def test_a_streak_milestone_is_celebrated_once():
    async def check(db, me):
        me.streak_days = 7
        achievements = AchievementService(db)

        await achievements._streak_milestone(me)
        await achievements._streak_milestone(me)  # evaluated again the same day

        return await streak_notes(db, me)

    assert with_db(check) == ["7-day streak! 🔥"]


def test_no_celebration_between_milestones():
    async def check(db, me):
        for days in (0, 1, 2, 4, 8, 29):
            me.streak_days = days
            await AchievementService(db)._streak_milestone(me)

        return await streak_notes(db, me)

    assert with_db(check) == []
    assert STREAK_MILESTONES >= {3, 7, 30}


def test_the_celebration_is_in_the_learners_language():
    async def check(db, me):
        me.streak_days = 14
        await AchievementService(db)._streak_milestone(me)

        return await streak_notes(db, me)

    assert with_db(check, language="ur-Latn") == ["14 din ki streak! 🔥"]
