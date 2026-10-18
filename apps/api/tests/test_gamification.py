from datetime import date, datetime, timezone

import pytest

from app.services.gamification_service import (
    level_for,
    local_today,
    next_streak,
)

TODAY = date(2026, 10, 18)


@pytest.mark.parametrize(
    "current,last,expected",
    [
        (0, None, 1),
        (3, date(2026, 10, 18), 3),
        (0, date(2026, 10, 18), 1),
        (3, date(2026, 10, 17), 4),
        (5, date(2026, 10, 16), 1),
        (5, date(2026, 9, 1), 1),
    ],
)
def test_next_streak(current, last, expected):
    assert next_streak(current, last, TODAY) == expected


def test_level_for():
    assert level_for(0) == 1
    assert level_for(99) == 1
    assert level_for(100) == 2
    assert level_for(250) == 3
    assert level_for(-5) == 1


def test_local_today_uses_profile_timezone():
    now = datetime(2026, 10, 17, 22, 0, tzinfo=timezone.utc)

    assert local_today("Asia/Karachi", now) == date(2026, 10, 18)
    assert local_today("UTC", now) == date(2026, 10, 17)


def test_local_today_falls_back_to_utc():
    now = datetime(2026, 10, 17, 22, 0, tzinfo=timezone.utc)

    assert local_today(None, now) == date(2026, 10, 17)
    assert local_today("Not/AZone", now) == date(2026, 10, 17)
