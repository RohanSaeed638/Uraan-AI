"""The roadmap engine against the real database (every test is rolled back):
background generation, regeneration, adaptation, pause / resume and versions.
The AI is replaced by a fake generator."""
import asyncio
import selectors
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.ai.schemas.roadmap_schema import RoadmapOutput
from app.models.enums import RoadmapStatus
from app.models.profile import Profile
from app.repositories.roadmap_content_repository import RoadmapContentRepository
from app.schemas.roadmap import AdaptRequest, RoadmapGenerateRequest
from app.services.roadmap_jobs import is_stale, run_job
from app.services.roadmap_service import RoadmapService


def output(*phases, title="Plan"):
    """phases: lists of (task title, hours) -> a RoadmapOutput."""
    return RoadmapOutput(
        title=title,
        description="desc",
        phases=[
            {
                "title": f"Phase {i}",
                "description": "d",
                "order": i,
                "estimated_weeks": 2,
                "milestones": [f"Milestone {i}"],
                "tasks": [
                    {
                        "title": name, "description": "t", "resource_links": [],
                        "difficulty": "easy", "estimated_hours": hours,
                    }
                    for name, hours in tasks
                ],
            }
            for i, tasks in enumerate(phases, start=1)
        ],
    )


class FakeGenerator:
    def __init__(self, result=None, boom=False):
        self.result, self.boom, self.adapt_args = result, boom, None

    async def generate(self, profile, data, career=None):
        if self.boom:
            raise RuntimeError("AI is down")
        return self.result

    async def adapt(self, profile, roadmap, **kwargs):
        if self.boom:
            raise RuntimeError("AI is down")
        self.adapt_args = kwargs
        return self.result


class _Session:
    """Lets run_job use the test's session without closing it."""

    def __init__(self, db):
        self.db = db

    async def __aenter__(self):
        return self.db

    async def __aexit__(self, *exc):
        return False


REQUEST = RoadmapGenerateRequest(
    career_slug="backend-engineer", career_stage="beginner", skill_level="beginner",
    learning_goal="Get a backend job", daily_hours=2, target_duration=6,
    learning_style="reading",
)


def with_db(fn):
    from app.core.config import settings

    async def run():
        engine = create_async_engine(settings.DATABASE_URL)
        try:
            async with engine.connect() as conn:
                trans = await conn.begin()
                db = AsyncSession(
                    bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False,
                )
                try:
                    profile = Profile(auth_user_id=uuid4(), full_name="Tester")
                    db.add(profile)
                    await db.flush()
                    return await fn(db, profile)
                finally:
                    await db.close()
                    await trans.rollback()
        finally:
            await engine.dispose()

    try:
        return asyncio.run(
            run(),
            loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()),
        )
    except OSError as exc:
        pytest.skip(f"database not reachable: {type(exc).__name__}")


async def job(db, roadmap_id, kind, generator, params=None):
    await run_job(
        roadmap_id, kind, params,
        session_factory=lambda: _Session(db), generator=generator,
    )


async def reload(db, roadmap_id):
    return await RoadmapContentRepository(db).load(roadmap_id)


def titles(roadmap):
    return [t.title for p in sorted(roadmap.phases, key=lambda p: p.order)
            for t in sorted(p.tasks, key=lambda t: t.order)]


async def build(db, profile, generator=None):
    """A finished, active roadmap with two phases."""
    service = RoadmapService(db)
    placeholder = await service.start_generation(profile.auth_user_id, REQUEST)
    await job(db, placeholder.id, "generate", generator or FakeGenerator(
        output([("A", 4), ("B", 4)], [("C", 4), ("D", 4)], title="First")
    ))
    return service, await reload(db, placeholder.id)


async def raises_409(coro):
    with pytest.raises(HTTPException) as info:
        await coro
    assert info.value.status_code == 409


# ---- generation -----------------------------------------------------------------


def test_generation_runs_in_the_background_and_fills_the_roadmap():
    async def check(db, profile):
        service = RoadmapService(db)

        placeholder = await service.start_generation(profile.auth_user_id, REQUEST)
        assert placeholder.status == RoadmapStatus.GENERATING
        assert placeholder.career_slug == "backend-engineer"
        assert placeholder.learning_goal == "Get a backend job"

        status = await service.get_status(placeholder.id, profile.auth_user_id)
        assert status["status"] == RoadmapStatus.GENERATING

        await job(db, placeholder.id, "generate", FakeGenerator(
            output([("A", 4), ("B", 4)], [("C", 4)], title="My plan")
        ))

        roadmap = await reload(db, placeholder.id)
        assert roadmap.status == RoadmapStatus.ACTIVE
        assert roadmap.title == "My plan"
        assert roadmap.generation_error is None
        assert titles(roadmap) == ["A", "B", "C"]

        first, second = sorted(roadmap.phases, key=lambda p: p.order)
        assert first.milestones == ["Milestone 1"]
        assert first.duration_weeks == 2
        # weeks are always filled in, and run on from phase to phase
        assert [t.week for t in sorted(first.tasks, key=lambda t: t.order)] == [1, 2]
        assert [t.week for t in second.tasks] == [3]

    with_db(check)


def test_a_new_roadmap_archives_the_previously_active_one():
    async def check(db, profile):
        service, first = await build(db, profile)
        assert first.status == RoadmapStatus.ACTIVE

        second_placeholder = await service.start_generation(profile.auth_user_id, REQUEST)
        await job(db, second_placeholder.id, "generate", FakeGenerator(output([("X", 2)])))

        assert (await reload(db, first.id)).status == RoadmapStatus.ARCHIVED
        assert (await reload(db, second_placeholder.id)).status == RoadmapStatus.ACTIVE

    with_db(check)


def test_failed_generation_is_recorded_not_raised():
    async def check(db, profile):
        service = RoadmapService(db)
        placeholder = await service.start_generation(profile.auth_user_id, REQUEST)
        # A failed job rolls the shared test session back, which expires
        # these objects, so keep the plain values.
        rid, uid = placeholder.id, profile.auth_user_id

        await job(db, rid, "generate", FakeGenerator(boom=True))

        status = await service.get_status(rid, uid)
        assert status["status"] == RoadmapStatus.FAILED
        assert "could not create" in status["error"]
        assert "AI is down" not in status["error"]  # no internal details leak

        # a failed roadmap no longer blocks starting another
        again = await service.start_generation(uid, REQUEST)
        assert again.status == RoadmapStatus.GENERATING

    with_db(check)


def test_only_one_generation_at_a_time():
    async def check(db, profile):
        service = RoadmapService(db)
        await service.start_generation(profile.auth_user_id, REQUEST)

        await raises_409(service.start_generation(profile.auth_user_id, REQUEST))

    with_db(check)


def test_a_lost_job_is_given_up_on():
    old = datetime.now(timezone.utc) - timedelta(minutes=30)
    fresh = datetime.now(timezone.utc)

    lost = SimpleNamespace(status=RoadmapStatus.GENERATING, updated_at=old)
    running = SimpleNamespace(status=RoadmapStatus.GENERATING, updated_at=fresh)
    done = SimpleNamespace(status=RoadmapStatus.ACTIVE, updated_at=old)

    assert is_stale(lost) and not is_stale(running) and not is_stale(done)

    async def check(db, profile):
        service = RoadmapService(db)
        placeholder = await service.start_generation(profile.auth_user_id, REQUEST)
        placeholder.updated_at = old
        await db.flush()

        status = await service.get_status(placeholder.id, profile.auth_user_id)

        assert status["status"] == RoadmapStatus.FAILED

    with_db(check)


# ---- regenerate / adapt / versions ---------------------------------------------------


def test_regenerate_replaces_the_plan_and_keeps_a_version():
    async def check(db, profile):
        service, roadmap = await build(db, profile)

        await service.start_regenerate(roadmap.id, profile.auth_user_id)
        mid = await reload(db, roadmap.id)
        assert mid.status == RoadmapStatus.GENERATING
        assert mid.status_before_job == "active"

        await job(db, roadmap.id, "regenerate", FakeGenerator(output([("N1", 3), ("N2", 3)], title="Second")))

        after = await reload(db, roadmap.id)
        assert after.status == RoadmapStatus.ACTIVE
        assert after.title == "Second"
        assert titles(after) == ["N1", "N2"]

        versions = await service.list_versions(roadmap.id, profile.auth_user_id)
        assert len(versions) == 1
        assert versions[0]["reason"] == "regenerate"
        assert (versions[0]["phases"], versions[0]["tasks"]) == (2, 4)

    with_db(check)


def test_failed_regenerate_leaves_everything_as_it_was():
    async def check(db, profile):
        service, roadmap = await build(db, profile)
        await service.pause(roadmap.id, profile.auth_user_id)

        await service.start_regenerate(roadmap.id, profile.auth_user_id)
        await job(db, roadmap.id, "regenerate", FakeGenerator(boom=True))

        after = await reload(db, roadmap.id)
        assert after.status == RoadmapStatus.PAUSED  # back to what it was
        assert titles(after) == ["A", "B", "C", "D"]
        assert "unchanged" in after.generation_error

    with_db(check)


def test_adapt_keeps_finished_work_and_replans_the_rest():
    async def check(db, profile):
        service, roadmap = await build(db, profile)

        done = sorted(roadmap.phases, key=lambda p: p.order)[0].tasks
        for task in done:
            task.completed = True
        await db.flush()

        generator = FakeGenerator(output([("New1", 3), ("New2", 3)]))
        request = AdaptRequest(reason="study_time", daily_hours=1, months_left=3)

        await service.start_adapt(roadmap.id, profile.auth_user_id, request)
        await job(db, roadmap.id, "adapt", generator, request.model_dump())

        after = await reload(db, roadmap.id)

        assert titles(after) == ["A", "B", "New1", "New2"]  # C and D were replanned
        assert all(t.completed for t in sorted(after.phases, key=lambda p: p.order)[0].tasks)
        assert [p.order for p in sorted(after.phases, key=lambda p: p.order)] == [1, 2]
        assert after.status == RoadmapStatus.ACTIVE
        assert after.daily_hours == 1

        # the AI was told what was done and what was left
        assert generator.adapt_args["completed"] == ["A", "B"]
        assert generator.adapt_args["unfinished"] == ["C", "D"]
        assert generator.adapt_args["daily_hours"] == 1
        assert generator.adapt_args["months_left"] == 3

        # new weeks carry on after the finished ones (A and B were weeks 1-2)
        new_weeks = [t.week for t in sorted(after.phases, key=lambda p: p.order)[1].tasks]
        assert min(new_weeks) >= 3

    with_db(check)


def test_adapt_needs_something_left_to_adapt():
    async def check(db, profile):
        service, roadmap = await build(db, profile)

        for phase in roadmap.phases:
            for task in phase.tasks:
                task.completed = True
        await db.flush()

        await raises_409(
            service.start_adapt(roadmap.id, profile.auth_user_id, AdaptRequest(reason="behind"))
        )

    with_db(check)


def test_restore_brings_back_an_older_plan_and_can_be_undone():
    async def check(db, profile):
        service, roadmap = await build(db, profile)
        rid, uid = roadmap.id, profile.auth_user_id

        await service.start_regenerate(rid, uid)
        await job(db, rid, "regenerate", FakeGenerator(output([("Z", 1)], title="Other")))
        assert titles(await reload(db, rid)) == ["Z"]

        # study time changed since; restoring brings the old plan's back
        changed = await reload(db, rid)
        changed.daily_hours = 7
        await db.flush()

        original = (await service.list_versions(rid, uid))[0]
        restored = await service.restore_version(rid, original["id"], uid)

        assert restored.daily_hours == 2

        assert [t.title for p in sorted(restored.phases, key=lambda p: p.order) for t in p.tasks] == ["A", "B", "C", "D"]
        assert restored.title == "First"

        reasons = [v["reason"] for v in await service.list_versions(rid, uid)]
        assert reasons == ["restore", "regenerate"]  # newest first: the undo point exists

    with_db(check)


def test_only_the_newest_versions_are_kept():
    async def check(db, profile):
        service, roadmap = await build(db, profile)
        contents = RoadmapContentRepository(db)
        current = await reload(db, roadmap.id)

        for _ in range(13):
            await contents.save_version(current, "adapt")
        await db.flush()

        versions = await contents.list_versions(roadmap.id)

        assert len(versions) == 10
        assert versions[0].version_number == 13

    with_db(check)


# ---- pause / resume / permissions -------------------------------------------------------


def test_pause_resume_and_the_single_active_rule():
    async def check(db, profile):
        service, first = await build(db, profile)

        await service.pause(first.id, profile.auth_user_id)
        assert (await reload(db, first.id)).status == RoadmapStatus.PAUSED
        await service.pause(first.id, profile.auth_user_id)  # pausing twice is harmless

        # another roadmap becomes active while the first is paused
        placeholder = await service.start_generation(profile.auth_user_id, REQUEST)
        await job(db, placeholder.id, "generate", FakeGenerator(output([("X", 2)])))
        assert (await reload(db, first.id)).status == RoadmapStatus.PAUSED  # not archived

        await service.resume(first.id, profile.auth_user_id)

        assert (await reload(db, first.id)).status == RoadmapStatus.ACTIVE
        assert (await reload(db, placeholder.id)).status == RoadmapStatus.ARCHIVED

        assert (await service.resume(first.id, profile.auth_user_id)).status == RoadmapStatus.ACTIVE  # idempotent
        await raises_409(service.resume(placeholder.id, profile.auth_user_id))  # archived, not paused

    with_db(check)


def test_only_active_roadmaps_can_be_paused():
    async def check(db, profile):
        service, roadmap = await build(db, profile)
        roadmap.status = RoadmapStatus.COMPLETED
        await db.flush()

        await raises_409(service.pause(roadmap.id, profile.auth_user_id))

    with_db(check)


def test_nobody_else_can_touch_my_roadmap():
    async def check(db, profile):
        service, roadmap = await build(db, profile)

        stranger = Profile(auth_user_id=uuid4(), full_name="Stranger")
        db.add(stranger)
        await db.flush()

        for call in (
            service.pause(roadmap.id, stranger.auth_user_id),
            service.resume(roadmap.id, stranger.auth_user_id),
            service.start_regenerate(roadmap.id, stranger.auth_user_id),
            service.list_versions(roadmap.id, stranger.auth_user_id),
            service.get_status(roadmap.id, stranger.auth_user_id),
        ):
            with pytest.raises(HTTPException) as info:
                await call
            assert info.value.status_code == 404

    with_db(check)


def test_current_and_calendar_ignore_a_roadmap_still_being_built():
    async def check(db, profile):
        service, roadmap = await build(db, profile)
        await service.start_generation(profile.auth_user_id, REQUEST)  # newer, empty

        current = await service.get_current(profile.auth_user_id)

        assert current.id == roadmap.id

    with_db(check)


def test_phases_and_tasks_stay_in_plan_order_after_updates():
    """Ticking a task rewrites its row; without an ORDER BY the plan came back
    shuffled."""
    async def check(db, profile):
        service, roadmap = await build(db, profile)
        rid = roadmap.id

        for phase in roadmap.phases:
            for task in phase.tasks:
                task.completed = True
                await db.flush()
                task.completed = False
                await db.flush()

        fresh = await reload(db, rid)  # no sorting here on purpose

        assert [p.title for p in fresh.phases] == ["Phase 1", "Phase 2"]
        assert [t.title for p in fresh.phases for t in p.tasks] == ["A", "B", "C", "D"]

    with_db(check)
