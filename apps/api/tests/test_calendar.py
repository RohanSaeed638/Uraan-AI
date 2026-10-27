"""The study calendar: availability, the .ics feed, moving lessons, the AI
schedule helper and missed-lesson roll-over."""
import asyncio
import json
import selectors
from datetime import date, datetime, time, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.ai.llm import AIUnavailableError
from app.ai.schemas.planner_schema import PlannerRules
from app.models.ai_request import AiRequest
from app.models.enums import CareerStage, LearningStyle, RoadmapStatus, SkillLevel
from app.models.notification import Notification
from app.models.planner import ScheduleOverride, SchedulePreference, ScheduleSnapshot
from app.models.profile import Profile
from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.models.task_learning_unit import LearningUnitType, TaskLearningUnit
from app.services.calendar_service import (
    CalendarService,
    _fold,
    availability_for,
    build_ics,
)
from app.services.gamification_service import local_today

ROADMAP = uuid4()


# ---- availability ---------------------------------------------------------------------------------


def profile(**over):
    base = dict(daily_hours=2, weekend_study=None, preferred_study_hours=None)
    base.update(over)
    return SimpleNamespace(**base)


def prefs(**over):
    base = dict(weekday_minutes={}, blocked_dates=[], start_time=None)
    base.update(over)
    return SimpleNamespace(**base)


def test_daily_hours_become_minutes_for_every_day():
    a = availability_for(profile(daily_hours=3), None, None)

    assert a.weekday_minutes == [180] * 7 and a.blocked == set()


def test_skipping_weekends_zeroes_saturday_and_sunday_only():
    a = availability_for(profile(weekend_study=False), None, None)

    assert a.weekday_minutes == [120, 120, 120, 120, 120, 0, 0]
    assert availability_for(profile(weekend_study=True), None, None).weekday_minutes == [120] * 7
    assert availability_for(profile(weekend_study=None), None, None).weekday_minutes == [120] * 7


def test_daily_hours_are_kept_sensible():
    assert availability_for(profile(daily_hours=0), None, None).weekday_minutes[0] == 120
    assert availability_for(profile(daily_hours=40), None, None).weekday_minutes[0] == 720


def test_what_the_learner_told_the_planner_overrides_the_defaults():
    p = prefs(weekday_minutes={"1": 30, "5": 0, "9": 50, "x": 5}, blocked_dates=["2026-11-05", "nonsense", None])

    a = availability_for(profile(weekend_study=None), None, p)

    assert a.weekday_minutes == [120, 30, 120, 120, 120, 0, 120]  # junk keys ignored
    assert a.blocked == {date(2026, 11, 5)}


def test_study_minutes_from_the_planner_are_clamped():
    a = availability_for(profile(), None, prefs(weekday_minutes={"0": 5000, "1": -5}))

    assert a.weekday_minutes[:2] == [720, 0]


def test_the_start_time_comes_from_the_most_specific_source():
    reminder = SimpleNamespace(reminder_time=time(7, 15))

    assert availability_for(profile(), reminder, None).start == time(7, 15)
    assert availability_for(profile(preferred_study_hours="evening"), reminder, None).start == time(19, 0)
    assert availability_for(profile(preferred_study_hours="flexible"), reminder, None).start == time(7, 15)
    assert availability_for(profile(preferred_study_hours="evening"), reminder, prefs(start_time=time(6, 0))).start == time(6, 0)
    assert availability_for(profile(), None, None).start == time(18, 0)


# ---- what the AI may change ---------------------------------------------------------------------------


TODAY = date(2026, 11, 2)


def rules(**over):
    base = dict(weekday_minutes={}, blocked_dates=[], start=None, summary="Done.")
    base.update(over)
    return PlannerRules(**base)


def test_ai_rules_map_weekday_names_to_numbers_and_ignore_nulls():
    weekday, blocked = rules(weekday_minutes={"mon": 45, "sat": 0, "tue": None, "Sunday": 20, "funday": 5}).rules_for(TODAY)

    assert weekday == {"0": 45, "5": 0, "6": 20}
    assert blocked == []


def test_ai_minutes_are_clamped():
    weekday, _ = rules(weekday_minutes={"mon": 99999, "tue": -3}).rules_for(TODAY)

    assert weekday == {"0": 720, "1": 0}


def test_ai_blocked_dates_must_be_real_in_range_and_unique():
    far = (TODAY + timedelta(days=200)).isoformat()
    _, blocked = rules(
        blocked_dates=["2026-11-09", "2026-11-09", "2026-11-01", far, "2026-02-30", "soon", "2026-11-04"]
    ).rules_for(TODAY)

    assert blocked == ["2026-11-04", "2026-11-09"]  # sorted; past, far, fake and repeated ones dropped


def test_at_most_sixty_blocked_dates():
    many = [(TODAY + timedelta(days=i)).isoformat() for i in range(100)]

    assert len(rules(blocked_dates=many).rules_for(TODAY)[1]) == 60


def test_the_start_must_be_a_known_part_of_the_day():
    assert rules(start="evening").start == "evening"

    with pytest.raises(ValidationError):
        rules(start="midnight")

    with pytest.raises(ValidationError):
        rules(summary="")


# ---- the .ics feed -----------------------------------------------------------------------------------------


def day(when, units, start=time(19, 0), end=time(19, 45)):
    return {"date": when, "start": start, "end": end, "minutes": 45, "units": units}


def planned(title="Intro, basics; part 1", minutes=45, start=time(19, 0), task="Learn HTTP"):
    return {"title": title, "minutes": minutes, "start": start, "task_title": task}


def uid(text):
    return next(line for line in text.split("\r\n") if line.startswith("UID:"))


def test_ics_has_one_event_per_study_day_at_the_planned_time():
    ics = build_ics(
        [day(date(2026, 10, 19), [planned()])], ROADMAP,
        now=datetime(2026, 10, 19, 6, 0, tzinfo=timezone.utc),
    )

    assert ics.startswith("BEGIN:VCALENDAR\r\n") and ics.endswith("END:VCALENDAR\r\n")
    assert ics.count("BEGIN:VEVENT") == 1
    assert "DTSTART:20261019T190000" in ics
    assert "DTEND:20261019T194500" in ics
    assert "SUMMARY:Study: Learn HTTP" in ics
    assert "Intro\\, basics\\; part 1" in ics  # commas and semicolons are escaped
    assert "19:00 Intro" in ics  # the description gives each lesson's time


def test_ics_event_id_follows_the_date_not_the_lessons():
    first = build_ics([day(date(2026, 10, 19), [planned("a")])], ROADMAP)
    later = build_ics([day(date(2026, 10, 19), [planned("b"), planned("c")])], ROADMAP)
    other_day = build_ics([day(date(2026, 10, 20), [planned("a")])], ROADMAP)

    assert uid(first) == uid(later) != uid(other_day)


def test_short_days_still_get_a_minimum_length_event():
    ics = build_ics([day(date(2026, 10, 19), [planned(minutes=5)], end=time(19, 5))], ROADMAP)

    assert "DTEND:20261019T193000" in ics


def test_an_empty_plan_is_an_empty_calendar():
    ics = build_ics([], None)

    assert "BEGIN:VEVENT" not in ics and ics.endswith("END:VCALENDAR\r\n")


def test_long_lines_are_folded_to_75_octets():
    for line in _fold("DESCRIPTION:" + "x" * 200):
        assert len(line.encode("utf-8")) <= 75

    parts = _fold("DESCRIPTION:" + "é" * 100)
    assert all(len(p.encode("utf-8")) <= 75 for p in parts)
    assert "".join(p[1:] if i else p for i, p in enumerate(parts)) == "DESCRIPTION:" + "é" * 100


# ---- the real database (rolled back) -------------------------------------------------------------------------------


def with_db(fn, **profile_fields):
    from app.core.config import settings

    async def run():
        engine = create_async_engine(settings.DATABASE_URL)
        try:
            async with engine.connect() as conn:
                trans = await conn.begin()
                db = AsyncSession(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)
                try:
                    me = Profile(
                        auth_user_id=uuid4(), full_name="Ayesha", daily_hours=1, xp=0, streak_days=0,
                        **profile_fields,
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
        return asyncio.run(run(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))
    except OSError as exc:
        pytest.skip(f"database not reachable: {type(exc).__name__}")


async def roadmap_with(db, me, minutes, status=RoadmapStatus.ACTIVE):
    roadmap = Roadmap(
        profile_id=me.id, title="Plan", description="d", status=status,
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

    units = []
    for order, length in enumerate(minutes, start=1):
        unit = TaskLearningUnit(
            task_id=task.id, day=order, order=1, type=LearningUnitType.READING,
            title=f"Lesson {order}", estimated_minutes=length, completed=False,
        )
        db.add(unit)
        units.append(unit)
    await db.flush()

    return roadmap, units


def lesson_titles(schedule):
    return [[u["title"] for u in d["units"]] for d in schedule["days"]]


def on(schedule, when):
    return next((d for d in schedule["days"] if d["date"] == when), None)


def today_for(me):
    return local_today(me.timezone)


def status_of(coro):
    async def run():
        with pytest.raises(HTTPException) as info:
            await coro
        return info.value.status_code

    return run()


def test_real_db_the_plan_fills_each_day_with_the_learners_minutes():
    async def check(db, me):
        await roadmap_with(db, me, [30, 30, 60, 60])

        schedule = await CalendarService(db).schedule(me.auth_user_id)
        today = today_for(me)

        assert lesson_titles(schedule) == [["Lesson 1", "Lesson 2"], ["Lesson 3"], ["Lesson 4"]]
        assert schedule["days"][0]["date"] == today and schedule["unscheduled"] == 0
        assert schedule["availability"]["weekday_minutes"] == [60] * 7
        assert schedule["preferences"]["active"] is False

        first = schedule["days"][0]
        assert first["minutes"] == 60 and first["start"] == time(18, 0)  # no preference: the default start
        assert [(u["start"], u["end"]) for u in first["units"]] == [(time(18, 0), time(18, 30)), (time(18, 30), time(19, 0))]

    with_db(check)


def test_real_db_a_learner_who_skips_weekends_gets_none():
    async def check(db, me):
        await roadmap_with(db, me, [60] * 10)

        schedule = await CalendarService(db).schedule(me.auth_user_id)

        assert all(d["date"].weekday() < 5 for d in schedule["days"])
        assert len(schedule["days"]) == 10

    with_db(check, weekend_study=False, preferred_study_hours="evening")


def test_real_db_the_preferred_time_of_day_sets_the_start():
    async def check(db, me):
        await roadmap_with(db, me, [30])

        day = (await CalendarService(db).schedule(me.auth_user_id))["days"][0]

        assert day["start"] == time(8, 0)

    with_db(check, preferred_study_hours="morning")


def test_real_db_no_roadmap_or_a_paused_one_means_an_empty_calendar():
    async def check(db, me):
        service = CalendarService(db)

        empty = await service.schedule(me.auth_user_id)
        assert empty["roadmap_id"] is None and empty["days"] == []

        await roadmap_with(db, me, [30, 30], status=RoadmapStatus.PAUSED)
        paused = await service.schedule(me.auth_user_id)
        assert paused["roadmap_id"] is None and paused["days"] == []

    with_db(check)


def test_real_db_moving_a_lesson_pins_it_and_the_rest_flow_around_it():
    async def check(db, me):
        _, units = await roadmap_with(db, me, [60, 60, 60])
        service = CalendarService(db)
        today = today_for(me)
        target = today + timedelta(days=5)

        schedule = await service.move(me.auth_user_id, units[0].id, target)

        moved = on(schedule, target)
        assert [u["title"] for u in moved["units"]] == ["Lesson 1"] and moved["units"][0]["pinned"] is True
        assert lesson_titles(schedule)[:2] == [["Lesson 2"], ["Lesson 3"]]  # the others moved up

        # moving it again changes the date, not the number of pins
        schedule = await service.move(me.auth_user_id, units[0].id, target + timedelta(days=1))
        assert on(schedule, target) is None and on(schedule, target + timedelta(days=1)) is not None
        pins = (await db.execute(select(ScheduleOverride).where(ScheduleOverride.profile_id == me.id))).scalars().all()
        assert len(pins) == 1

        # unpinning lets the planner place it again, in order
        schedule = await service.unpin(me.auth_user_id, units[0].id)
        assert lesson_titles(schedule) == [["Lesson 1"], ["Lesson 2"], ["Lesson 3"]]

    with_db(check)


def test_real_db_a_lesson_cannot_be_moved_into_the_past_or_far_future():
    async def check(db, me):
        _, units = await roadmap_with(db, me, [30])
        service = CalendarService(db)
        today = today_for(me)

        assert await status_of(service.move(me.auth_user_id, units[0].id, today - timedelta(days=1))) == 422
        assert await status_of(service.move(me.auth_user_id, units[0].id, today + timedelta(days=400))) == 422
        await service.move(me.auth_user_id, units[0].id, today)  # today itself is fine

    with_db(check)


def test_real_db_only_your_own_unfinished_lessons_can_be_moved():
    async def check(db, me):
        _, units = await roadmap_with(db, me, [30, 30])
        units[1].completed = True
        await db.flush()

        stranger = Profile(auth_user_id=uuid4(), full_name="Other", daily_hours=1)
        db.add(stranger)
        await db.flush()
        _, theirs = await roadmap_with(db, stranger, [30])

        service = CalendarService(db)
        tomorrow = today_for(me) + timedelta(days=1)

        assert await status_of(service.move(me.auth_user_id, units[1].id, tomorrow)) == 409  # finished
        assert await status_of(service.move(me.auth_user_id, theirs[0].id, tomorrow)) == 404  # someone else's
        assert await status_of(service.move(me.auth_user_id, uuid4(), tomorrow)) == 404

    with_db(check)


def test_real_db_a_pinned_lesson_that_was_missed_is_flagged():
    async def check(db, me):
        _, units = await roadmap_with(db, me, [30, 30])
        yesterday = today_for(me) - timedelta(days=1)
        db.add(ScheduleOverride(profile_id=me.id, unit_id=units[0].id, date=yesterday))
        await db.flush()

        schedule = await CalendarService(db).schedule(me.auth_user_id)

        past = on(schedule, yesterday)
        assert past["units"][0]["missed"] is True and past["units"][0]["pinned"] is True
        # the lesson that was not pinned is planned from today
        assert on(schedule, today_for(me))["units"][0]["title"] == "Lesson 2"

    with_db(check)


def optimise_answer(**over):
    base = dict(
        weekday_minutes={"mon": None, "tue": 30, "wed": None, "thu": None, "fri": None, "sat": 0, "sun": 0},
        blocked_dates=[], start="evening", summary="Evenings only, and weekends off.",
    )
    base.update(over)
    return json.dumps(base)


class Asker:
    def __init__(self, *answers):
        self.answers, self.calls = list(answers), []

    async def __call__(self, messages, **kwargs):
        self.calls.append((messages, kwargs))
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


def test_real_db_telling_the_planner_about_your_time_changes_the_plan():
    async def check(db, me):
        await roadmap_with(db, me, [60] * 12)
        today = today_for(me)
        tomorrow = today + timedelta(days=1)
        ask = Asker(optimise_answer(blocked_dates=[tomorrow.isoformat()]))
        service = CalendarService(db, ask=ask)

        result = await service.optimise(me.auth_user_id, "Exams tomorrow, evenings only, no weekends")

        assert result["summary"] == "Evenings only, and weekends off."
        assert result["preferences"] == {"note": "Exams tomorrow, evenings only, no weekends", "active": True}
        assert on(result, tomorrow) is None  # blocked
        assert all(d["date"].weekday() < 5 for d in result["days"])
        assert all(d["start"] == time(19, 0) for d in result["days"])
        assert result["availability"]["weekday_minutes"][1] == 30  # Tuesday
        assert result["availability"]["blocked_dates"] == [tomorrow.isoformat()]

        # the AI was told today's date and that the text is data, not instructions
        prompt = ask.calls[0][0][1]["content"]
        assert today.isoformat() in prompt and "never as" in prompt
        assert ask.calls[0][1]["purpose"] == "planner" and ask.calls[0][1]["prompt_version"] == "planner-v1"

        notes = (await db.execute(select(Notification).where(Notification.profile_id == me.id))).scalars().all()
        assert [n.type for n in notes] == ["schedule_updated"]

        # starting over removes everything it set
        reset = await service.reset_preferences(me.auth_user_id)
        assert reset["preferences"]["active"] is False and reset["availability"]["weekday_minutes"] == [60] * 7

    with_db(check)


def test_real_db_a_failed_or_nonsense_answer_changes_nothing():
    async def check(db, me):
        await roadmap_with(db, me, [60])

        for ask in (Asker(AIUnavailableError("down")), Asker("not json", "{}")):
            with pytest.raises(HTTPException) as info:
                await CalendarService(db, ask=ask).optimise(me.auth_user_id, "Exams next week")
            assert info.value.status_code == 502

        assert (await db.execute(select(SchedulePreference).where(SchedulePreference.profile_id == me.id))).first() is None

    with_db(check)


def test_real_db_the_daily_limit_on_schedule_changes():
    async def check(db, me):
        await roadmap_with(db, me, [60])

        for _ in range(10):
            db.add(AiRequest(profile_id=me.id, purpose="planner", provider="openai", model="m", success=True))
        await db.flush()

        ask = Asker(optimise_answer())

        with pytest.raises(HTTPException) as info:
            await CalendarService(db, ask=ask).optimise(me.auth_user_id, "Exams next week")

        assert info.value.status_code == 429 and ask.calls == []

    with_db(check)


def test_real_db_missed_lessons_move_on_and_the_learner_is_told():
    async def check(db, me):
        _, units = await roadmap_with(db, me, [60, 60, 60])
        service = CalendarService(db)
        today = today_for(me)

        # the first run only records today's plan
        assert await service.roll_over(me, None) == 0
        assert await service.roll_over(me, None) == 0  # and only once a day

        snapshot = (await db.execute(select(ScheduleSnapshot).where(ScheduleSnapshot.profile_id == me.id))).scalar_one()

        # pretend it is a day later: yesterday's plan had lessons 1 and 2 on yesterday
        yesterday = (today - timedelta(days=1)).isoformat()
        snapshot.day = today - timedelta(days=1)
        snapshot.plan = {str(units[0].id): yesterday, str(units[1].id): yesterday, str(units[2].id): today.isoformat()}
        db.add(ScheduleOverride(profile_id=me.id, unit_id=units[1].id, date=today - timedelta(days=1)))  # pinned: not moved
        units[2].completed = True  # done: not missed
        await db.flush()

        assert await service.roll_over(me, None) == 1  # only lesson 1: unpinned, unfinished, overdue

        note = (await db.execute(select(Notification).where(Notification.profile_id == me.id))).scalar_one()
        assert note.type == "schedule_updated" and "moved 1 lesson" in note.title
        assert note.dedupe_key == f"rollover:{today.isoformat()}"

        assert await service.roll_over(me, None) == 0  # not again today

    with_db(check)


def test_real_db_the_feed_uses_the_plan_and_hides_missed_days():
    async def check(db, me):
        _, units = await roadmap_with(db, me, [60, 60])
        me.calendar_token = "tok-" + uuid4().hex
        db.add(ScheduleOverride(profile_id=me.id, unit_id=units[0].id, date=today_for(me) - timedelta(days=2)))
        await db.flush()

        ics = await CalendarService(db).feed(me.calendar_token)
        today = today_for(me)

        assert ics.count("BEGIN:VEVENT") == 1  # the missed pinned day is not an event
        assert f"DTSTART:{today.strftime('%Y%m%d')}T180000" in ics
        assert "Lesson 2" in ics and "Lesson 1" not in ics

        with pytest.raises(HTTPException) as info:
            await CalendarService(db).feed("wrong-token")
        assert info.value.status_code == 404

    with_db(check)
