"""The top-bar search, against the real database (rolled back afterwards)."""
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
from app.services.search_service import PER_KIND, SearchService, like_pattern, result_url

WORD = f"zq{uuid4().hex[:8]}"  # a word nothing else in the database contains


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


async def learner(db, conn, name="Search Test"):
    auth_id = uuid4()
    await conn.execute(text("insert into auth.users (id, email) values (:i, :e)"), {"i": auth_id, "e": f"{auth_id}@x.test"})
    me = Profile(auth_user_id=auth_id, full_name=name, daily_hours=1, xp=0, streak_days=0, language="en")
    db.add(me)
    await db.flush()
    return auth_id, me


async def plan(db, me, roadmap_title, task_title, unit_title):
    roadmap = Roadmap(
        profile_id=me.id, title=roadmap_title, description="d", status=RoadmapStatus.ACTIVE,
        career_slug="backend-engineer", career_stage=CareerStage.BEGINNER, skill_level=SkillLevel.BEGINNER,
        learning_goal="job", learning_style=LearningStyle.READING, daily_hours=1, target_duration=6,
    )
    db.add(roadmap)
    await db.flush()
    phase = RoadmapPhase(roadmap_id=roadmap.id, order=1, title="P", description="d", duration_weeks=2)
    db.add(phase)
    await db.flush()
    task = RoadmapTask(phase_id=phase.id, title=task_title, order=1, completed=False)
    db.add(task)
    await db.flush()
    unit = TaskLearningUnit(
        task_id=task.id, day=1, order=1, type=LearningUnitType.READING, title=unit_title,
        estimated_minutes=20, completed=False, status="ready",
    )
    db.add(unit)
    await db.flush()
    return roadmap, task, unit


def test_a_learner_finds_their_own_roadmap_task_lesson_document_and_chat():
    async def check(db, conn):
        auth_id, me = await learner(db, conn)
        roadmap, task, unit = await plan(db, me, f"{WORD} roadmap", f"Task {WORD}", f"Lesson {WORD} basics")
        db.add(Document(profile_id=me.id, kind="resume", title=f"Resume {WORD}", content="c"))
        chat = MentorConversation(profile_id=me.id, title=f"Chat about {WORD}")
        db.add(chat)
        await db.flush()
        found = await SearchService(db).search(auth_id, WORD.upper())  # not case sensitive

        return roadmap, task, unit, chat, found

    roadmap, task, unit, chat, found = with_db(check)
    by_kind = {r["kind"]: r for r in found}

    assert [r["kind"] for r in found] == ["roadmap", "task", "lesson", "document", "conversation"]
    assert by_kind["roadmap"]["url"] == f"/roadmaps/{roadmap.id}"
    assert by_kind["task"]["url"] == f"/roadmaps/{roadmap.id}/task/{task.id}"
    assert by_kind["lesson"]["url"] == f"/roadmaps/{roadmap.id}/task/{task.id}/learn/{unit.id}"
    assert by_kind["conversation"]["url"] == f"/mentor?c={chat.id}"
    assert by_kind["document"]["url"].startswith("/resume?d=")
    assert by_kind["task"]["subtitle"] == f"{WORD} roadmap" and by_kind["lesson"]["subtitle"] == f"Task {WORD}"


def test_nobody_sees_anyone_elses_titles():
    async def check(db, conn):
        mine_auth, me = await learner(db, conn, "Mine")
        _, other = await learner(db, conn, "Other")
        await plan(db, other, f"{WORD} theirs", f"Task {WORD}", f"Lesson {WORD}")
        db.add(Document(profile_id=other.id, kind="resume", title=f"Theirs {WORD}", content="c"))
        db.add(MentorConversation(profile_id=other.id, title=f"Theirs {WORD}"))
        await db.flush()

        return await SearchService(db).search(mine_auth, WORD)

    assert with_db(check) == []


def test_careers_are_found_by_name_or_address_and_inactive_ones_are_not():
    async def check(db, conn):
        auth_id, _ = await learner(db, conn)
        found = await SearchService(db).search(auth_id, "backend")
        inactive = await conn.execute(text("select count(*) from careers where is_active = false"))

        return found, inactive.scalar_one()

    found, _ = with_db(check)
    careers = [r for r in found if r["kind"] == "career"]

    assert careers and all(r["url"].startswith("/careers/") for r in careers)


def test_too_short_or_empty_searches_return_nothing_without_touching_the_database():
    async def check(db, conn):
        auth_id, _ = await learner(db, conn)
        service = SearchService(db)

        return [await service.search(auth_id, q) for q in ("", " ", "a", "  b ")]

    assert with_db(check) == [[], [], [], []]


def test_a_percent_sign_or_underscore_is_searched_for_literally():
    async def check(db, conn):
        auth_id, me = await learner(db, conn)
        await plan(db, me, "Plain roadmap", "Task", "Unit")
        db.add(Document(profile_id=me.id, kind="resume", title=f"Raise 50% {WORD}", content="c"))
        await db.flush()
        service = SearchService(db)

        return await service.search(auth_id, "50%"), await service.search(auth_id, "%%"), await service.search(auth_id, "_ _")

    percent, wildcard, underscores = with_db(check)

    assert [r["kind"] for r in percent] == ["document"]
    assert wildcard == [] and underscores == []


def test_each_kind_is_capped_so_one_source_cannot_fill_the_list():
    async def check(db, conn):
        auth_id, me = await learner(db, conn)

        for i in range(PER_KIND + 4):
            db.add(Document(profile_id=me.id, kind="resume", title=f"Doc {WORD} {i}", content="c"))

        await db.flush()

        return await SearchService(db).search(auth_id, WORD)

    assert len(with_db(check)) == PER_KIND


def test_an_account_without_a_profile_finds_nothing():
    async def check(db, conn):
        return await SearchService(db).search(uuid4(), "backend")

    assert with_db(check) == []


def test_the_pattern_escapes_wildcards():
    assert like_pattern("50%") == "%50\\%%"
    assert like_pattern("a_b") == "%a\\_b%"
    assert like_pattern("c:\\x") == "%c:\\\\x%"


def test_every_kind_has_a_page_to_open():
    from types import SimpleNamespace

    row = SimpleNamespace(id="i", roadmap_id="r", task_id="t", slug="backend-engineer", title="CS50")

    assert result_url("career", row) == "/careers/backend-engineer"
    assert result_url("resource", row) == "/resources?q=CS50"
    assert result_url("lesson", row) == "/roadmaps/r/task/t/learn/i"
