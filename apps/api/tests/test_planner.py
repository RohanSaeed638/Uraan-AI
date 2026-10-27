from datetime import date, time
from uuid import uuid4

import pytest

from app.services.planner import (
    Availability,
    PlanUnit,
    clamp_daily_minutes,
    plan,
    start_for,
)

MON = date(2026, 11, 2)      # a Monday
FRI = date(2026, 11, 6)
TASK = uuid4()


def unit(minutes=30, completed=False, title=None):
    return PlanUnit(
        id=uuid4(), task_id=TASK, task_title="Task", title=title or f"L{minutes}",
        type="reading", minutes=minutes, completed=completed,
    )


def week(minutes=60, **over):
    days = [minutes] * 7
    for key, value in over.items():
        days["mon tue wed thu fri sat sun".split().index(key)] = value
    return Availability(weekday_minutes=days)


def titles(result):
    return [[p.unit.title for p in d.placed] for d in result.days]


def dates(result):
    return [d.date for d in result.days]


# ---- filling days ------------------------------------------------------------------------------


def test_lessons_fill_a_day_then_continue_on_the_next():
    a, b, c = unit(30, title="a"), unit(30, title="b"), unit(60, title="c")

    result = plan([a, b, c], MON, week(60))

    assert titles(result) == [["a", "b"], ["c"]]
    assert dates(result) == [MON, date(2026, 11, 3)]
    assert result.unscheduled == []


def test_a_lesson_is_never_split_and_order_is_kept():
    items = [unit(45, title="a"), unit(45, title="b"), unit(45, title="c")]

    result = plan(items, MON, week(60))

    assert titles(result) == [["a"], ["b"], ["c"]]  # 45 + 45 does not fit in 60


def test_a_small_lesson_after_a_big_one_waits_its_turn():
    # b does not fit after a, and c must not jump ahead of b
    result = plan([unit(50, title="a"), unit(30, title="b"), unit(10, title="c")], MON, week(60))

    assert titles(result) == [["a"], ["b", "c"]]


def test_missing_lengths_count_as_thirty_minutes():
    result = plan([unit(None, title="a"), unit(None, title="b"), unit(None, title="c")], MON, week(60))

    assert titles(result) == [["a", "b"], ["c"]]


def test_a_lesson_longer_than_a_day_takes_a_day_alone():
    result = plan([unit(30, title="a"), unit(200, title="big"), unit(30, title="b")], MON, week(60))

    assert titles(result) == [["a"], ["big"], ["b"]]


def test_completed_lessons_are_not_planned():
    result = plan([unit(30, completed=True), unit(30, title="todo")], MON, week(60))

    assert titles(result) == [["todo"]]


def test_nothing_to_plan():
    assert plan([], MON, week(60)).days == []
    assert plan([unit(30, completed=True)], MON, week(60)).days == []


# ---- availability ------------------------------------------------------------------------------------


def test_weekends_can_be_skipped():
    items = [unit(60, title=str(i)) for i in range(3)]

    result = plan(items, FRI, week(60, sat=0, sun=0))

    assert dates(result) == [FRI, date(2026, 11, 9), date(2026, 11, 10)]  # Fri, Mon, Tue


def test_blocked_dates_are_skipped():
    avail = week(60)
    avail.blocked = {date(2026, 11, 3)}

    result = plan([unit(60), unit(60)], MON, avail)

    assert dates(result) == [MON, date(2026, 11, 4)]


def test_different_minutes_on_different_days():
    result = plan([unit(30, title=str(i)) for i in range(5)], MON, week(30, tue=90))

    assert titles(result) == [["0"], ["1", "2", "3"], ["4"]]


def test_no_study_time_at_all_terminates_and_reports_it():
    items = [unit(30), unit(30)]

    result = plan(items, MON, week(0))

    assert result.days == [] and result.unscheduled == items


def test_a_plan_starts_today_even_if_today_is_a_weekend():
    sat = date(2026, 11, 7)

    result = plan([unit(30)], sat, week(60, sat=0, sun=0))

    assert dates(result) == [date(2026, 11, 9)]


# ---- pinned lessons -----------------------------------------------------------------------------------------


def test_a_pinned_lesson_stays_on_its_date_and_uses_its_minutes():
    a, b, c = unit(60, title="a"), unit(60, title="b"), unit(60, title="c")
    friday = date(2026, 11, 6)

    result = plan([a, b, c], MON, week(60), pinned={b.id: friday})

    by_date = dict(zip(dates(result), titles(result)))
    assert by_date[friday] == ["b"]
    assert by_date[MON] == ["a"] and by_date[date(2026, 11, 3)] == ["c"]


def test_loose_lessons_fill_around_a_pinned_one_on_the_same_day():
    a, b, c = unit(30, title="a"), unit(30, title="b"), unit(30, title="c")

    result = plan([a, b, c], MON, week(60), pinned={c.id: MON})

    # c is pinned to Monday (30 of 60 minutes); only one loose lesson fits there
    assert titles(result)[0] == ["a", "c"]
    assert titles(result)[1] == ["b"]


def test_lessons_in_a_day_are_in_lesson_order_pinned_or_not():
    a, b, c = unit(20, title="a"), unit(20, title="b"), unit(20, title="c")

    result = plan([a, b, c], MON, week(120), pinned={b.id: MON})

    assert titles(result) == [["a", "b", "c"]]


def test_pinned_lessons_can_overfill_a_day_because_the_learner_chose_it():
    a, b = unit(90, title="a"), unit(90, title="b")

    result = plan([a, b], MON, week(60), pinned={a.id: MON, b.id: MON})

    assert titles(result) == [["a", "b"]]
    assert result.days[0].minutes == 180


def test_a_pinned_lesson_whose_date_passed_is_shown_as_missed():
    a, b = unit(30, title="a"), unit(30, title="b")
    yesterday = date(2026, 10, 30)

    result = plan([a, b], MON, week(60), pinned={a.id: yesterday})

    assert dates(result)[0] == yesterday
    assert result.days[0].placed[0].missed and result.days[0].placed[0].pinned
    # the lesson that was not pinned is planned from today, not left behind
    assert titles(result)[1] == ["b"] and dates(result)[1] == MON


def test_a_pinned_lesson_on_a_skipped_day_is_still_kept():
    sat = date(2026, 11, 7)
    a = unit(30, title="a")

    result = plan([a], MON, week(60, sat=0), pinned={a.id: sat})

    assert dates(result) == [sat]


def test_a_pinned_completed_lesson_is_ignored():
    a = unit(30, completed=True)

    assert plan([a], MON, week(60), pinned={a.id: MON}).days == []


# ---- time of day ------------------------------------------------------------------------------------------------


def avail_at(start, minutes=240):
    a = week(minutes)
    a.start = start
    return a


def test_a_block_starts_at_the_preferred_time_and_lessons_follow_each_other():
    result = plan([unit(30, title="a"), unit(45, title="b")], MON, avail_at(time(19, 0)))

    day = result.days[0]

    assert (day.start, day.end, day.minutes) == (time(19, 0), time(20, 15), 75)
    assert [(p.start, p.end) for p in day.placed] == [(time(19, 0), time(19, 30)), (time(19, 30), time(20, 15))]


def test_a_late_block_is_moved_earlier_instead_of_running_past_the_night():
    result = plan([unit(120), unit(120)], MON, avail_at(time(21, 0), 240))

    day = result.days[0]

    assert day.end <= time(23, 30)
    assert day.start == time(19, 30)  # 4 hours back from 23:30
    assert (day.placed[-1].end) == day.end


def test_a_huge_block_never_runs_past_midnight():
    result = plan([unit(700)], MON, avail_at(time(21, 0), 720))

    day = result.days[0]

    assert day.start >= time(5, 0) and day.end <= time(23, 59)


@pytest.mark.parametrize(
    "part, expected",
    [("morning", time(8, 0)), ("afternoon", time(14, 0)), ("evening", time(19, 0)), ("night", time(21, 0))],
)
def test_parts_of_day_have_start_times(part, expected):
    assert start_for(part) == expected


def test_flexible_or_unknown_uses_the_reminder_time_then_a_default():
    assert start_for("flexible", time(9, 30)) == time(9, 30)
    assert start_for(None, time(7, 0)) == time(7, 0)
    assert start_for(None) == time(18, 0)
    assert start_for("whenever") == time(18, 0)


@pytest.mark.parametrize("raw, clamped", [(None, 120), (5, 30), (90, 90), (99999, 720)])
def test_daily_minutes_are_kept_sensible(raw, clamped):
    assert clamp_daily_minutes(raw) == clamped
