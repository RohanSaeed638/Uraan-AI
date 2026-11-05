"""Deleting a learner on request: everything of theirs goes, nobody else's does. Real database, rolled back."""
import asyncio
import selectors
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.document import Document
from app.models.enums import CareerStage, LearningStyle, RoadmapStatus, SkillLevel
from app.models.mentor_conversation import MentorConversation
from app.models.profile import Profile
from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.models.task_learning_unit import LearningUnitType, TaskLearningUnit
from app.models.xp_event import XPEvent
from app.services.account_deletion import delete_learner


def with_db(fn):
    async def go():
        async with engine.connect() as conn:
            outer = await conn.begin()
            db = AsyncSession(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)

            try:
                return await fn(db, conn)
            finally:
                await db.close()
                await outer.rollback()

    try:
        return asyncio.run(go(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))
    except OSError:
        pytest.skip("database not reachable")


async def learner(db, conn, name):
    auth_id = uuid4()
    await conn.execute(text("insert into auth.users (id, email) values (:i, :e)"), {"i": auth_id, "e": f"{auth_id}@x.test"})
    me = Profile(auth_user_id=auth_id, full_name=name, daily_hours=1, xp=0, streak_days=0, language="en")
    db.add(me)
    await db.flush()
    roadmap = Roadmap(
        profile_id=me.id, title=f"{name} plan", description="d", status=RoadmapStatus.ACTIVE,
        career_slug="backend-engineer", career_stage=CareerStage.BEGINNER, skill_level=SkillLevel.BEGINNER,
        learning_goal="job", learning_style=LearningStyle.READING, daily_hours=1, target_duration=6,
    )
    db.add(roadmap)
    await db.flush()
    phase = RoadmapPhase(roadmap_id=roadmap.id, order=1, title="P", description="d", duration_weeks=2)
    db.add(phase)
    await db.flush()
    task = RoadmapTask(phase_id=phase.id, title="T", order=1, completed=False)
    db.add(task)
    await db.flush()
    db.add(TaskLearningUnit(task_id=task.id, day=1, order=1, type=LearningUnitType.READING, title="L",
                            estimated_minutes=10, completed=False, status="ready"))
    db.add(Document(profile_id=me.id, kind="resume", title="CV", content="c"))
    db.add(MentorConversation(profile_id=me.id, title="Chat"))
    db.add(XPEvent(profile_id=me.id, amount=10, reason="lesson", ref_id=uuid4()))
    await db.flush()

    return auth_id, me


async def count(conn, table, column, value):
    return (await conn.execute(text(f"select count(*) from {table} where {column} = :v"), {"v": value})).scalar_one()


def test_everything_of_the_learner_goes_including_the_login():
    async def check(db, conn):
        auth_id, me = await learner(db, conn, "Leaving")
        deleted = await delete_learner(conn, auth_id)

        return (
            deleted,
            await count(conn, "profiles", "id", me.id),
            await count(conn, "roadmaps", "profile_id", me.id),
            await count(conn, "documents", "profile_id", me.id),
            await count(conn, "mentor_conversations", "profile_id", me.id),
            await count(conn, "xp_events", "profile_id", me.id),
            await count(conn, "auth.users", "id", auth_id),
        )

    deleted, *remaining = with_db(check)

    assert remaining == [0, 0, 0, 0, 0, 0]
    assert deleted["profiles"] == 1 and deleted["roadmaps"] == 1 and deleted["task_learning_units"] == 1
    assert deleted["auth.users"] == 1


def test_another_learners_data_is_untouched():
    async def check(db, conn):
        leaving_auth, leaving = await learner(db, conn, "Leaving")
        staying_auth, staying = await learner(db, conn, "Staying")
        await delete_learner(conn, leaving_auth)

        return (
            await count(conn, "profiles", "id", staying.id),
            await count(conn, "roadmaps", "profile_id", staying.id),
            await count(conn, "documents", "profile_id", staying.id),
            await count(conn, "auth.users", "id", staying_auth),
        )

    assert with_db(check) == (1, 1, 1, 1)


def test_the_login_can_be_kept():
    async def check(db, conn):
        auth_id, me = await learner(db, conn, "Keep login")
        deleted = await delete_learner(conn, auth_id, remove_login=False)

        return deleted, await count(conn, "auth.users", "id", auth_id)

    deleted, logins = with_db(check)

    assert "auth.users" not in deleted and logins == 1


def test_an_unknown_account_deletes_nothing():
    async def check(db, conn):
        return await delete_learner(conn, uuid4())

    assert with_db(check) == {}
