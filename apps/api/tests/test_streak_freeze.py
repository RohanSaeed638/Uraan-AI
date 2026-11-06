"""Streak freezes: miss a day and a freeze keeps the streak, one is earned every 7 days."""
import asyncio
import selectors
from datetime import date, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.gamification_service import (
    FREEZE_EVERY_DAYS,
    MAX_FREEZES,
    GamificationService,
    advance_streak,
    next_streak,
    streak_state,
)

TODAY = date(2026, 11, 5)

# Every test starts with XP awarding stubbed out (see conftest.py); these tests want the real one.
REAL_AWARD = GamificationService.award


def days_ago(n):
    return TODAY - timedelta(days=n)


# ---- advancing --------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "current,last,freezes,expected",
    [
        (0, None, 0, (1, 0)),                       # the very first day
        (3, days_ago(0), 1, (3, 1)),                # the same day again changes nothing
        (3, days_ago(1), 0, (4, 0)),                # the next day extends it
        (3, days_ago(2), 0, (1, 0)),                # one missed day and no freeze: it breaks
        (3, days_ago(2), 1, (4, 0)),                # one missed day, one freeze: used up, streak goes on
        (3, days_ago(2), 2, (4, 1)),                # a spare freeze is kept
        (3, days_ago(3), 1, (1, 1)),                # two missed days, one freeze: not enough, and it is not wasted
        (3, days_ago(3), 2, (4, 0)),                # two freezes cover two missed days
        (3, days_ago(4), 2, (1, 2)),                # three missed days: broken, freezes kept
        (5, date(2026, 9, 1), 2, (1, 2)),           # long gone: starts again
    ],
)
def test_advancing_the_streak(current, last, freezes, expected):
    assert advance_streak(current, last, TODAY, freezes) == expected


def test_a_freeze_is_earned_when_the_streak_reaches_a_multiple_of_seven():
    assert advance_streak(6, days_ago(1), TODAY, 0) == (7, 1)
    assert advance_streak(13, days_ago(1), TODAY, 1) == (14, 2)


def test_no_more_than_two_freezes_are_kept():
    assert advance_streak(20, days_ago(1), TODAY, MAX_FREEZES) == (21, MAX_FREEZES)


def test_studying_twice_in_a_day_does_not_earn_a_second_freeze():
    streak, freezes = advance_streak(6, days_ago(1), TODAY, 0)
    again = advance_streak(streak, TODAY, TODAY, freezes)

    assert (streak, freezes) == (7, 1) and again == (7, 1)


def test_bridging_a_missed_day_can_also_earn_the_next_freeze():
    # 6-day streak, one missed day covered by a freeze: the streak reaches 7 and earns one back.
    assert advance_streak(6, days_ago(2), TODAY, 1) == (7, 1)


def test_the_old_rule_without_freezes_is_unchanged():
    assert [next_streak(c, l, TODAY) for c, l in ((0, None), (3, days_ago(0)), (3, days_ago(1)), (5, days_ago(2)))] == [1, 3, 4, 1]


def test_the_constants_say_what_the_app_tells_learners():
    assert FREEZE_EVERY_DAYS == 7 and MAX_FREEZES == 2


# ---- what the learner is shown ------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "current,last,freezes,expected",
    [
        (0, None, 2, (0, False)),
        (5, days_ago(0), 0, (5, False)),     # studied today
        (5, days_ago(1), 0, (5, False)),     # studied yesterday: today is not over yet
        (5, days_ago(2), 0, (0, False)),     # a whole day missed and no freeze: gone
        (5, days_ago(2), 1, (5, True)),      # held up by a freeze
        (5, days_ago(3), 1, (0, False)),     # two missed, one freeze: gone
        (5, days_ago(3), 2, (5, True)),
        (0, days_ago(1), 2, (0, False)),     # nothing to protect
    ],
)
def test_the_streak_shown_and_whether_a_freeze_is_holding_it(current, last, freezes, expected):
    assert streak_state(current, last, TODAY, freezes) == expected


# ---- through the service ----------------------------------------------------------------------------------------------


class Db:
    def __init__(self):
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)

        class Result:
            def scalar_one_or_none(self_inner):
                return uuid4()  # "this XP was newly awarded"

            def scalar_one(self_inner):
                return 0

        return Result()

    async def flush(self):
        pass


def run(coro):
    return asyncio.run(coro, loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))


def learner(**over):
    values = dict(
        id=uuid4(), xp=0, streak_days=6, streak_freezes=0, last_activity_date=None, timezone="UTC",
    )
    values.update(over)
    return SimpleNamespace(**values)


def test_awarding_xp_moves_the_streak_and_earns_a_freeze(monkeypatch):
    from app.services import gamification_service as module

    monkeypatch.setattr(module, "local_today", lambda tz: TODAY)
    me = learner(streak_days=6, last_activity_date=days_ago(1))
    run(REAL_AWARD(GamificationService(Db()), me, 10, "lesson_completed", uuid4(), evaluate=False))

    assert (me.streak_days, me.streak_freezes, me.last_activity_date) == (7, 1, TODAY)


def test_awarding_xp_after_a_missed_day_uses_a_freeze(monkeypatch):
    from app.services import gamification_service as module

    monkeypatch.setattr(module, "local_today", lambda tz: TODAY)
    me = learner(streak_days=4, streak_freezes=1, last_activity_date=days_ago(2))
    run(REAL_AWARD(GamificationService(Db()), me, 10, "lesson_completed", uuid4(), evaluate=False))

    assert (me.streak_days, me.streak_freezes) == (5, 0)


def test_the_summary_reports_freezes_and_protection(monkeypatch):
    from app.services import gamification_service as module

    monkeypatch.setattr(module, "local_today", lambda tz: TODAY)

    async def no_weekly(self, profile):
        return 0

    monkeypatch.setattr(GamificationService, "weekly_xp", no_weekly)
    me = learner(streak_days=9, streak_freezes=1, last_activity_date=days_ago(2))
    summary = run(GamificationService(Db()).summary(me))

    assert summary["streak_days"] == 9 and summary["streak_freezes"] == 1 and summary["streak_protected"] is True
    assert summary["active_today"] is False
