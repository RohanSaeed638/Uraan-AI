"""Lessons written behind the plan: claiming, filling in, failing, retrying.

These use the real database and really commit (the writer opens its own
sessions, as it does in production), then delete everything they made."""
import asyncio
import selectors
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.ai.schemas.learning_plan_schema import PlanUnit
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.enums import CareerStage, LearningStyle, RoadmapStatus, SkillLevel
from app.models.profile import Profile
from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.models.task_learning_unit import LearningUnitType, TaskLearningUnit
from app.services.lesson_writer import needs_writer, plan_of, requeue_failed, write_pending_lessons

FK_SQL = text(
    "select c.conrelid::regclass::text, a.attname from pg_constraint c "
    "join pg_attribute a on a.attrelid = c.conrelid and a.attnum = c.conkey[1] "
    "where c.contype = 'f' and c.confrelid = cast(:parent as regclass)"
)


def run(coro):
    return asyncio.run(coro, loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))


async def purge(conn, table, where_sql, params):
    for child, col in (await conn.execute(FK_SQL, {"parent": table})).all():
        await purge(conn, child, f"{col} in (select id from {table} where {where_sql})", params)

    await conn.execute(text(f"delete from {table} where {where_sql}"), params)


class Writer:
    """Stands in for the AI: writes a lesson, or fails for chosen titles."""

    def __init__(self, fail=()):
        self.fail, self.seen, self.active, self.peak = set(fail), [], 0, 0

    async def write_unit(self, unit, units, roadmap, task):
        self.seen.append(unit.title)
        self.active += 1
        self.peak = max(self.peak, self.active)
        await asyncio.sleep(0.05)
        self.active -= 1

        if unit.title in self.fail:
            raise ValueError("the AI gave nothing usable")

        return f"Body of {unit.title}", ({"difficulty": "beginner"} if unit.type == "project" else None)


def with_task(fn, kinds=("reading", "reading", "project", "reading", "reading", "exercise")):
    async def go():
        pid = uuid4()

        async with SessionLocal() as db:
            me = Profile(auth_user_id=uuid4(), full_name="Writer Test", daily_hours=1, xp=0, streak_days=0, language="en")
            db.add(me)
            await db.flush()
            roadmap = Roadmap(
                profile_id=me.id, title="Plan", description="d", status=RoadmapStatus.ACTIVE,
                career_slug="backend-engineer", career_stage=CareerStage.BEGINNER,
                skill_level=SkillLevel.BEGINNER, learning_goal="job",
                learning_style=LearningStyle.READING, daily_hours=1, target_duration=6,
            )
            db.add(roadmap)
            await db.flush()
            phase = RoadmapPhase(roadmap_id=roadmap.id, order=1, title="P", description="d", duration_weeks=2)
            db.add(phase)
            await db.flush()
            task = RoadmapTask(phase_id=phase.id, title="Learn HTTP", order=1, completed=False)
            db.add(task)
            await db.flush()

            for i, kind in enumerate(kinds, start=1):
                db.add(
                    TaskLearningUnit(
                        task_id=task.id, day=(i + 1) // 2, order=(i + 1) % 2 + 1, type=LearningUnitType(kind),
                        title=f"Lesson {i}", estimated_minutes=20, completed=False, status="pending",
                        details={"_plan": PlanUnit(
                            day=(i + 1) // 2, order=(i + 1) % 2 + 1, type=kind, title=f"Lesson {i}",
                            estimated_minutes=20, outline=["a point"], language="python" if kind == "exercise" else None,
                        ).model_dump()},
                    )
                )

            await db.commit()
            pid, task_id = me.id, task.id

        try:
            return await fn(task_id)
        finally:
            engine = create_async_engine(settings.DATABASE_URL)

            async with engine.begin() as conn:
                await purge(conn, "profiles", "id = :p", {"p": pid})

            await engine.dispose()

    try:
        return run(go())
    except OSError as exc:
        pytest.skip(f"database not reachable: {type(exc).__name__}")


async def rows(task_id):
    async with SessionLocal() as db:
        return list(
            (
                await db.execute(
                    select(TaskLearningUnit).where(TaskLearningUnit.task_id == task_id).order_by(
                        TaskLearningUnit.day, TaskLearningUnit.order
                    )
                )
            ).scalars()
        )


def test_every_waiting_lesson_gets_written_and_marked_ready():
    async def check(task_id):
        writer = Writer()
        counts = await write_pending_lessons(task_id, generator=writer)

        return counts, [(r.status, r.content) for r in await rows(task_id)], writer

    counts, saved, writer = with_task(check)

    assert counts == {"written": 6, "failed": 0}
    assert [s for s, _ in saved] == ["ready"] * 6
    assert saved[0][1] == "Body of Lesson 1" and saved[5][1] == "Body of Lesson 6"
    assert sorted(writer.seen) == [f"Lesson {i}" for i in range(1, 7)]


def test_the_first_days_are_written_first():
    async def check(task_id):
        writer = Writer()
        await write_pending_lessons(task_id, generator=writer)

        return writer.seen

    seen = with_task(check)

    # Writers take lessons in order, so day 1 is always in the first wave and the last lesson never is.
    assert {"Lesson 1", "Lesson 2"} <= set(seen[:4])
    assert "Lesson 6" not in seen[:4]


def test_only_a_few_are_written_at_once():
    async def check(task_id):
        writer = Writer()
        await write_pending_lessons(task_id, generator=writer)

        return writer.peak

    assert 1 < with_task(check) <= 4


def test_a_lesson_that_fails_is_marked_failed_and_the_others_still_finish():
    async def check(task_id):
        counts = await write_pending_lessons(task_id, generator=Writer(fail={"Lesson 3"}))

        return counts, [(r.title, r.status, r.content) for r in await rows(task_id)]

    counts, saved = with_task(check)

    assert counts == {"written": 5, "failed": 1}
    assert [t for t, s, c in saved if s == "failed"] == ["Lesson 3"]
    assert next(c for t, s, c in saved if t == "Lesson 3") is None
    assert [s for t, s, c in saved if t != "Lesson 3"] == ["ready"] * 5


def test_a_failed_lesson_can_be_retried():
    async def check(task_id):
        await write_pending_lessons(task_id, generator=Writer(fail={"Lesson 2"}))

        async with SessionLocal() as db:
            requeued = await requeue_failed(db, task_id)
            await db.commit()

        retry = Writer()
        counts = await write_pending_lessons(task_id, generator=retry)

        return requeued, counts, retry.seen, [r.status for r in await rows(task_id)]

    requeued, counts, seen, statuses = with_task(check)

    assert requeued == 1 and counts == {"written": 1, "failed": 0}
    assert seen == ["Lesson 2"]  # nothing already written is written again
    assert statuses == ["ready"] * 6


def test_two_writers_never_write_the_same_lesson():
    async def check(task_id):
        a, b = Writer(), Writer()
        counts = await asyncio.gather(
            write_pending_lessons(task_id, generator=a), write_pending_lessons(task_id, generator=b)
        )

        return counts, a.seen + b.seen, [r.status for r in await rows(task_id)]

    counts, seen, statuses = with_task(check)

    assert sum(c["written"] for c in counts) == 6
    assert sorted(seen) == [f"Lesson {i}" for i in range(1, 7)]  # each exactly once
    assert statuses == ["ready"] * 6


def test_a_writer_that_died_leaves_lessons_another_can_take_over():
    async def check(task_id):
        stale = datetime.now(timezone.utc) - timedelta(minutes=10)
        fresh = datetime.now(timezone.utc)

        async with SessionLocal() as db:
            units = await rows(task_id)
            # Lesson 1 was claimed ten minutes ago and never finished; lesson 2 is being written right now.
            await db.execute(
                text("update task_learning_units set status='writing', updated_at=:t where id=:i"),
                {"t": stale, "i": units[0].id},
            )
            await db.execute(
                text("update task_learning_units set status='writing', updated_at=:t where id=:i"),
                {"t": fresh, "i": units[1].id},
            )
            await db.commit()

        writer = Writer()
        await write_pending_lessons(task_id, generator=writer)

        return writer.seen, [r.status for r in await rows(task_id)]

    seen, statuses = with_task(check)

    assert "Lesson 1" in seen and "Lesson 2" not in seen
    assert statuses[1] == "writing" and statuses[0] == "ready"


def test_a_task_that_does_not_exist_is_ignored():
    assert run(write_pending_lessons(uuid4(), generator=Writer())) == {"written": 0, "failed": 0}


# ---- small pieces -------------------------------------------------------------------------------------------------------


def test_needs_writer_sees_waiting_and_abandoned_lessons():
    now = datetime.now(timezone.utc)

    def unit(status, age=0):
        return SimpleNamespace(status=status, updated_at=now - timedelta(minutes=age))

    assert needs_writer([unit("ready"), unit("pending")]) is True
    assert needs_writer([unit("ready"), unit("writing", 1)]) is False  # someone is on it
    assert needs_writer([unit("writing", 10)]) is True  # nobody is
    assert needs_writer([unit("ready"), unit("failed")]) is False  # waits for the learner to retry
    assert needs_writer([]) is False


def test_the_saved_outline_is_read_back_and_finished_lessons_get_a_bare_one():
    saved = PlanUnit(day=2, order=1, type="reading", title="HTTP", estimated_minutes=25, outline=["verbs"])
    waiting = SimpleNamespace(details={"_plan": saved.model_dump()}, day=2, order=1, type=LearningUnitType.READING,
                              title="x", description=None, estimated_minutes=25)
    done = SimpleNamespace(details=None, day=3, order=2, type=LearningUnitType.PROJECT, title="Build it",
                           description=None, estimated_minutes=None)

    assert plan_of(waiting).outline == ["verbs"] and plan_of(waiting).title == "HTTP"
    assert (plan_of(done).day, plan_of(done).title, plan_of(done).type) == (3, "Build it", "project")
