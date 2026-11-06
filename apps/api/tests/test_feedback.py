"""Lesson feedback: one vote each, only on your own lessons. Real database, rolled back."""
import asyncio
import selectors
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.enums import CareerStage, LearningStyle, RoadmapStatus, SkillLevel
from app.models.profile import Profile
from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.models.task_learning_unit import LearningUnitType, TaskLearningUnit
from app.schemas.feedback import FeedbackRequest
from app.services.feedback_service import FeedbackService


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


async def learner_with_lesson(db, conn, name="Voter"):
    auth_id = uuid4()
    await conn.execute(text("insert into auth.users (id, email) values (:i, :e)"), {"i": auth_id, "e": f"{auth_id}@x.test"})
    me = Profile(auth_user_id=auth_id, full_name=name, daily_hours=1, xp=0, streak_days=0, language="en")
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
    task = RoadmapTask(phase_id=phase.id, title="Learn HTTP", order=1, completed=False)
    db.add(task)
    await db.flush()
    unit = TaskLearningUnit(task_id=task.id, day=1, order=1, type=LearningUnitType.READING, title="HTTP verbs",
                            estimated_minutes=20, completed=False, status="ready")
    db.add(unit)
    await db.flush()

    return auth_id, unit


async def rows(conn, unit_id):
    return (
        await conn.execute(
            text("select helpful, reason, comment, career_slug, task_title, lesson_title, lesson_type "
                 "from lesson_feedback where unit_id = :u"),
            {"u": unit_id},
        )
    ).all()


def test_a_not_helpful_vote_is_saved_with_its_reason_and_what_the_lesson_was():
    async def check(db, conn):
        auth_id, unit = await learner_with_lesson(db, conn)
        saved = await FeedbackService(db).save(
            unit.id, FeedbackRequest(helpful=False, reason="wrong", comment="  The verb table is wrong  "), auth_id
        )

        return saved, await rows(conn, unit.id)

    saved, stored = with_db(check)

    assert (saved.helpful, saved.reason, saved.comment) == (False, "wrong", "The verb table is wrong")
    assert [tuple(r) for r in stored] == [
        (False, "wrong", "The verb table is wrong", "backend-engineer", "Learn HTTP", "HTTP verbs", "reading")
    ]


def test_voting_again_replaces_the_vote_it_does_not_add_one():
    async def check(db, conn):
        auth_id, unit = await learner_with_lesson(db, conn)
        service = FeedbackService(db)
        await service.save(unit.id, FeedbackRequest(helpful=False, reason="unclear"), auth_id)
        await service.save(unit.id, FeedbackRequest(helpful=True), auth_id)

        return await rows(conn, unit.id), await service.get(unit.id, auth_id)

    stored, current = with_db(check)

    assert len(stored) == 1 and stored[0][0] is True
    assert current.helpful is True and current.reason is None


def test_a_reason_or_comment_on_a_helpful_vote_is_dropped():
    async def check(db, conn):
        auth_id, unit = await learner_with_lesson(db, conn)

        return await FeedbackService(db).save(
            unit.id, FeedbackRequest(helpful=True, reason="wrong", comment="nice"), auth_id
        )

    saved = with_db(check)

    assert saved.reason is None and saved.comment is None


def test_a_blank_comment_is_stored_as_nothing():
    async def check(db, conn):
        auth_id, unit = await learner_with_lesson(db, conn)

        return await FeedbackService(db).save(unit.id, FeedbackRequest(helpful=False, comment="   "), auth_id)

    assert with_db(check).comment is None


def test_the_vote_can_be_read_back_and_withdrawn():
    async def check(db, conn):
        auth_id, unit = await learner_with_lesson(db, conn)
        service = FeedbackService(db)
        before = await service.get(unit.id, auth_id)
        await service.save(unit.id, FeedbackRequest(helpful=True), auth_id)
        during = await service.get(unit.id, auth_id)
        await service.clear(unit.id, auth_id)

        return before, during, await service.get(unit.id, auth_id)

    before, during, after = with_db(check)

    assert before is None and during.helpful is True and after is None


def test_nobody_can_vote_on_someone_elses_lesson():
    async def check(db, conn):
        _, theirs = await learner_with_lesson(db, conn, "Owner")
        stranger_auth, _ = await learner_with_lesson(db, conn, "Stranger")
        service = FeedbackService(db)
        outcomes = []

        for call in (
            service.save(theirs.id, FeedbackRequest(helpful=False), stranger_auth),
            service.get(theirs.id, stranger_auth),
            service.clear(theirs.id, stranger_auth),
        ):
            try:
                await call
                outcomes.append("allowed")
            except HTTPException as exc:
                outcomes.append(exc.status_code)

        return outcomes, await rows(conn, theirs.id)

    outcomes, stored = with_db(check)

    assert outcomes == [404, 404, 404] and stored == []


def test_an_unknown_lesson_or_account_is_a_404():
    async def check(db, conn):
        auth_id, _ = await learner_with_lesson(db, conn)
        statuses = []

        for call in (
            FeedbackService(db).get(uuid4(), auth_id),
            FeedbackService(db).get(uuid4(), uuid4()),
        ):
            try:
                await call
            except HTTPException as exc:
                statuses.append(exc.status_code)

        return statuses

    assert with_db(check) == [404, 404]


def test_a_vote_survives_when_its_lesson_is_deleted():
    async def check(db, conn):
        auth_id, unit = await learner_with_lesson(db, conn)
        await FeedbackService(db).save(unit.id, FeedbackRequest(helpful=False, reason="wrong"), auth_id)
        unit_id = unit.id
        await conn.execute(text("delete from task_learning_units where id = :u"), {"u": unit_id})

        return (
            await conn.execute(text("select unit_id, lesson_title from lesson_feedback where lesson_title = 'HTTP verbs' and unit_id is null"))
        ).all()

    assert len(with_db(check)) >= 1


@pytest.mark.parametrize(
    "bad",
    [{"helpful": False, "reason": "boring"}, {"helpful": True, "extra": 1}, {"helpful": False, "comment": "x" * 501}, {}],
)
def test_bad_requests_are_refused_before_anything_is_saved(bad):
    with pytest.raises(ValidationError):
        FeedbackRequest(**bad)
