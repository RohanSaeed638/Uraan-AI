from datetime import date, datetime, time, timezone
from uuid import uuid4

from app.schemas.learning import (
    LearningAgendaDayResponse,
    LearningAgendaUnitResponse,
)
from app.services.calendar_service import _fold, build_ics, build_schedule

ROADMAP = uuid4()


def unit(title, completed=False, minutes=30):
    return LearningAgendaUnitResponse(
        id=uuid4(),
        roadmap_id=ROADMAP,
        task_id=uuid4(),
        task_title="Learn HTTP",
        title=title,
        type="reading",
        order=1,
        estimated_minutes=minutes,
        completed=completed,
    )


def day(number, units):
    return LearningAgendaDayResponse(
        day=number,
        units=units,
        total_estimated_minutes=sum(u.estimated_minutes or 0 for u in units),
    )


def test_finished_days_are_skipped_and_rest_start_today():
    days = [
        day(1, [unit("done", completed=True)]),
        day(2, [unit("half", completed=True), unit("todo")]),
        day(3, [unit("later")]),
    ]

    schedule = build_schedule(days, date(2026, 10, 19))

    assert [d.day for d in schedule] == [2, 3]
    assert [d.date for d in schedule] == [
        date(2026, 10, 19),
        date(2026, 10, 20),
    ]


def test_empty_plan_gives_empty_schedule():
    assert build_schedule([], date(2026, 10, 19)) == []


def test_ics_has_one_event_per_day_at_reminder_time():
    schedule = build_schedule(
        [day(1, [unit("Intro, basics; part 1", minutes=45)])],
        date(2026, 10, 19),
    )

    ics = build_ics(
        schedule,
        ROADMAP,
        "Roadmap",
        time(9, 0),
        now=datetime(2026, 10, 19, 6, 0, tzinfo=timezone.utc),
    )

    assert ics.startswith("BEGIN:VCALENDAR\r\n")
    assert ics.endswith("END:VCALENDAR\r\n")
    assert ics.count("BEGIN:VEVENT") == 1
    assert "DTSTART:20261019T090000" in ics
    assert "DTEND:20261019T094500" in ics
    # commas and semicolons in text must be escaped
    assert "Intro\\, basics\\; part 1" in ics


def test_ics_event_uid_is_stable_for_the_same_day_of_study():
    days = [day(1, [unit("a")])]

    first = build_ics(build_schedule(days, date(2026, 10, 19)), ROADMAP, "R", time(9, 0))
    later = build_ics(build_schedule(days, date(2026, 10, 25)), ROADMAP, "R", time(9, 0))

    def uid(text):
        return next(l for l in text.split("\r\n") if l.startswith("UID:"))

    assert uid(first) == uid(later)


def test_short_days_still_get_a_minimum_length_event():
    schedule = build_schedule([day(1, [unit("tiny", minutes=5)])], date(2026, 10, 19))

    ics = build_ics(schedule, ROADMAP, "R", time(9, 0))

    assert "DTEND:20261019T093000" in ics


def test_long_lines_are_folded_to_75_octets():
    for line in _fold("DESCRIPTION:" + "x" * 200):
        assert len(line.encode("utf-8")) <= 75

    parts = _fold("DESCRIPTION:" + "é" * 100)
    assert all(len(p.encode("utf-8")) <= 75 for p in parts)
    assert "".join(p[1:] if i else p for i, p in enumerate(parts)) == (
        "DESCRIPTION:" + "é" * 100
    )
