from datetime import datetime, time, timezone

import pytest

from app.services.reminder_service import (
    daily_message,
    is_due,
    local_now,
    weekly_message,
)


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "now,reminder,tz,expected",
    [
        # 09:10 UTC, reminder 09:00 UTC -> inside the 30 minute window
        (utc(2026, 10, 19, 9, 10), time(9, 0), "UTC", True),
        (utc(2026, 10, 19, 9, 29), time(9, 0), "UTC", True),
        (utc(2026, 10, 19, 9, 30), time(9, 0), "UTC", False),
        # before the reminder time
        (utc(2026, 10, 19, 8, 59), time(9, 0), "UTC", False),
        # 04:05 UTC is 09:05 in Karachi (UTC+5)
        (utc(2026, 10, 19, 4, 5), time(9, 0), "Asia/Karachi", True),
        (utc(2026, 10, 19, 9, 5), time(9, 0), "Asia/Karachi", False),
        # across midnight: reminder 23:50, now 00:10 local
        (utc(2026, 10, 19, 0, 10), time(23, 50), "UTC", True),
        # unknown timezone falls back to UTC
        (utc(2026, 10, 19, 9, 5), time(9, 0), "Not/AZone", True),
        (utc(2026, 10, 19, 9, 5), time(9, 0), None, True),
    ],
)
def test_is_due(now, reminder, tz, expected):
    assert is_due(now, reminder, tz) is expected


def test_no_daily_reminder_after_studying():
    local = local_now("UTC", utc(2026, 10, 20, 9, 0))

    assert daily_message(5, True, local) is None


def test_daily_reminder_mentions_streak_at_risk():
    local = local_now("UTC", utc(2026, 10, 20, 9, 0))

    message = daily_message(5, False, local)

    assert "5-day streak" in message.title
    assert message.dedupe_key == "2026-10-20"


def test_daily_reminder_without_streak():
    local = local_now("UTC", utc(2026, 10, 20, 9, 0))

    message = daily_message(0, False, local)

    assert message.title == "Time to study"


def test_weekly_summary_only_on_monday():
    monday = local_now("UTC", utc(2026, 10, 19, 9, 0))
    tuesday = local_now("UTC", utc(2026, 10, 20, 9, 0))

    assert weekly_message(40, tuesday) is None

    message = weekly_message(40, monday)

    assert "40 XP" in message.body
    assert message.dedupe_key == "2026-W43"
