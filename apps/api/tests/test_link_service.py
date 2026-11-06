"""Taking dead links out of learners' tasks, and the weekly sweep. Real database, rolled back; no real websites."""
import asyncio
import selectors
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import engine
from app.models.enums import CareerStage, LearningStyle, RoadmapStatus, SkillLevel
from app.models.library import LibraryResource
from app.models.link_check import LinkCheck
from app.models.profile import Profile
from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.services import link_service
from app.services.link_checker import DEAD, OK, UNKNOWN, LinkResult, fallback_link
from app.services.link_service import dead_among, repair_roadmap_links, repair_tasks, sweep

STAMP = uuid4().hex[:8]


def url(name):
    return f"https://{STAMP}.example.com/{name}"


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


class Web:
    """A pretend checker: answers from a table, defaults to ok, and remembers what it was asked."""

    def __init__(self, **answers):
        self.answers = {url(name): status for name, status in answers.items()}
        self.asked = []

    async def __call__(self, urls):
        self.asked.extend(urls)

        return {u: LinkResult(self.answers.get(u, OK), 404 if self.answers.get(u) == DEAD else 200, "test") for u in urls}


async def roadmap_with_tasks(db, conn, links_per_task):
    auth_id = uuid4()
    await conn.execute(text("insert into auth.users (id, email) values (:i, :e)"), {"i": auth_id, "e": f"{auth_id}@x.test"})
    me = Profile(auth_user_id=auth_id, full_name="Links", daily_hours=1, xp=0, streak_days=0, language="en")
    db.add(me)
    await db.flush()
    roadmap = Roadmap(
        profile_id=me.id, title="Plan", description="d", status=RoadmapStatus.ACTIVE, career_slug="backend-engineer",
        career_stage=CareerStage.BEGINNER, skill_level=SkillLevel.BEGINNER, learning_goal="job",
        learning_style=LearningStyle.READING, daily_hours=1, target_duration=6,
    )
    db.add(roadmap)
    await db.flush()
    phase = RoadmapPhase(roadmap_id=roadmap.id, order=1, title="P", description="d", duration_weeks=2)
    db.add(phase)
    await db.flush()
    tasks = []

    for i, links in enumerate(links_per_task, start=1):
        task = RoadmapTask(phase_id=phase.id, title=f"Topic {i}", order=i, completed=False, resource_links=links)
        db.add(task)
        tasks.append(task)

    await db.flush()

    return roadmap, tasks


# ---- repairing tasks -----------------------------------------------------------------------------------------------------


def test_dead_links_are_removed_and_good_ones_kept():
    async def check(db, conn):
        _, (task,) = await roadmap_with_tasks(db, conn, [[url("good"), url("gone"), url("fine")]])
        summary = await repair_tasks(db, [task], Web(gone=DEAD))

        return task.resource_links, summary

    links, summary = with_db(check)

    assert links == [url("good"), url("fine")]
    assert summary == {"checked": 3, "removed": 1, "tasks_changed": 1}


def test_a_task_left_with_no_working_link_gets_a_search_for_its_topic():
    async def check(db, conn):
        _, (task,) = await roadmap_with_tasks(db, conn, [[url("gone1"), url("gone2")]])
        await repair_tasks(db, [task], Web(gone1=DEAD, gone2=DEAD))

        return task.resource_links

    assert with_db(check) == [fallback_link("Topic 1")]


def test_doubtful_links_are_left_alone():
    async def check(db, conn):
        _, (task,) = await roadmap_with_tasks(db, conn, [[url("blocked"), url("slow")]])
        summary = await repair_tasks(db, [task], Web(blocked=UNKNOWN, slow=UNKNOWN))

        return task.resource_links, summary["removed"]

    links, removed = with_db(check)

    assert links == [url("blocked"), url("slow")] and removed == 0


def test_search_links_and_tasks_without_links_are_never_touched():
    async def check(db, conn):
        search = "https://www.google.com/search?q=python+tutorial"
        _, tasks = await roadmap_with_tasks(db, conn, [[search], [], None])
        web = Web()
        summary = await repair_tasks(db, tasks, web)

        return [t.resource_links for t in tasks], web.asked, summary

    links, asked, summary = with_db(check)

    assert links == [["https://www.google.com/search?q=python+tutorial"], [], None]
    assert asked == [] and summary["removed"] == 0


# ---- the shared memory of results ----------------------------------------------------------------------------------------


def test_a_recent_result_is_reused_instead_of_asking_the_website_again():
    async def check(db, conn):
        web = Web(gone=DEAD)
        first = await dead_among(db, [url("gone"), url("good")], web)
        asked_first = len(web.asked)
        second = await dead_among(db, [url("gone"), url("good")], web)

        return first, second, asked_first, len(web.asked)

    first, second, asked_first, asked_total = with_db(check)

    assert first == second == {url("gone")}
    assert asked_first == 2 and asked_total == 2  # nothing was asked the second time


def test_an_old_result_is_checked_again_and_a_repeat_failure_is_counted():
    async def check(db, conn):
        web = Web(gone=DEAD)
        await dead_among(db, [url("gone")], web)
        await db.execute(text("update link_checks set checked_at = now() - interval '10 days' where url = :u"), {"u": url("gone")})
        await dead_among(db, [url("gone")], web)
        row = (await db.execute(text("select fail_count, status from link_checks where url = :u"), {"u": url("gone")})).one()

        return len(web.asked), tuple(row)

    asked, row = with_db(check)

    assert asked == 2 and row == (2, "dead")


def test_a_link_that_answers_again_has_its_failures_forgiven():
    async def check(db, conn):
        await dead_among(db, [url("back")], Web(back=DEAD))
        await db.execute(text("update link_checks set checked_at = now() - interval '10 days' where url = :u"), {"u": url("back")})
        await dead_among(db, [url("back")], Web())  # answers fine now

        return tuple((await db.execute(text("select fail_count, status from link_checks where url = :u"), {"u": url("back")})).one())

    assert with_db(check) == (0, "ok")


# ---- after a roadmap is built --------------------------------------------------------------------------------------------


class Session:
    """Hands the test's own (rolled back) session to code that opens its own."""

    def __init__(self, db):
        self.db = db

    def __call__(self):
        return self

    async def __aenter__(self):
        return self.db

    async def __aexit__(self, *exc):
        return False


def test_a_new_roadmap_has_its_dead_links_taken_out(monkeypatch):
    monkeypatch.setattr(settings, "LINK_CHECK_ENABLED", True)

    async def check(db, conn):
        roadmap, tasks = await roadmap_with_tasks(db, conn, [[url("a"), url("dead")], [url("b")]])
        summary = await repair_roadmap_links(roadmap.id, Session(db), Web(dead=DEAD))

        return summary, [t.resource_links for t in tasks]

    summary, links = with_db(check)

    assert summary["removed"] == 1 and links == [[url("a")], [url("b")]]


def test_nothing_is_checked_when_the_switch_is_off(monkeypatch):
    monkeypatch.setattr(settings, "LINK_CHECK_ENABLED", False)
    web = Web()

    async def check(db, conn):
        roadmap, _ = await roadmap_with_tasks(db, conn, [[url("a")]])

        return await repair_roadmap_links(roadmap.id, Session(db), web)

    assert with_db(check) is None and web.asked == []


def test_a_failure_while_checking_never_reaches_the_caller(monkeypatch):
    monkeypatch.setattr(settings, "LINK_CHECK_ENABLED", True)

    async def broken(urls):
        raise RuntimeError("network down")

    async def check(db, conn):
        roadmap, tasks = await roadmap_with_tasks(db, conn, [[url("a")]])
        result = await repair_roadmap_links(roadmap.id, Session(db), broken)

        return result, tasks[0].resource_links

    result, links = with_db(check)

    assert result is None and links == [url("a")]


# ---- the weekly sweep ----------------------------------------------------------------------------------------------------


def test_the_sweep_removes_dead_links_from_tasks_and_switches_off_library_resources_that_stay_dead():
    async def check(db, conn):
        _, (task,) = await roadmap_with_tasks(db, conn, [[url("task-gone"), url("task-ok")]])
        stays_dead = LibraryResource(title="Gone course", url=url("lib-gone"), type="course", is_active=True)
        fine = LibraryResource(title="Fine course", url=url("lib-ok"), type="course", is_active=True)
        db.add_all([stays_dead, fine])
        await db.flush()
        web = Web(**{"task-gone": DEAD, "lib-gone": DEAD})

        first = await sweep(db, limit=100_000, checker=web)
        still_on_after_one = (await db.execute(text("select is_active from library_resources where url = :u"), {"u": url("lib-gone")})).scalar_one()

        # A second weekly check finds it dead again: now it is switched off.
        await db.execute(text("update link_checks set checked_at = now() - interval '10 days' where url like :p"), {"p": f"%{STAMP}%"})
        second = await sweep(db, limit=100_000, checker=web)
        states = {
            u: (await db.execute(text("select is_active from library_resources where url = :u"), {"u": url(u)})).scalar_one()
            for u in ("lib-gone", "lib-ok")
        }

        return first, second, still_on_after_one, states, task.resource_links

    first, second, still_on, states, task_links = with_db(check)

    assert still_on is True  # one failure is not enough
    assert states == {"lib-gone": False, "lib-ok": True}
    assert task_links == [url("task-ok")]
    assert first["dead_links_removed"] >= 1 and second["library_switched_off"] >= 1


def test_the_sweep_leaves_recently_checked_links_alone():
    async def check(db, conn):
        await roadmap_with_tasks(db, conn, [[url("fresh")]])
        await sweep(db, limit=100_000, checker=Web())
        web = Web()
        await sweep(db, limit=100_000, checker=web)

        return [u for u in web.asked if STAMP in u]

    assert with_db(check) == []
