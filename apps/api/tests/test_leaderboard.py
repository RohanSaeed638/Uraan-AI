from datetime import datetime, timezone

import pytest

from app.services.leaderboard_service import display_name, week_start


@pytest.mark.parametrize(
    "full_name,expected",
    [
        ("Rohan Saeed", "Rohan S."),
        ("rohan  ali khan", "rohan K."),
        ("Madonna", "Madonna"),
        ("", "Learner"),
        (None, "Learner"),
        ("   ", "Learner"),
    ],
)
def test_display_name_hides_full_names(full_name, expected):
    assert display_name(full_name) == expected


def test_week_start_is_monday_midnight_utc():
    # Sunday 18 Oct 2026 -> Monday 12 Oct 2026
    sunday = datetime(2026, 10, 18, 15, 30, tzinfo=timezone.utc)

    assert week_start(sunday) == datetime(2026, 10, 12, tzinfo=timezone.utc)
    assert week_start(week_start(sunday)) == week_start(sunday)
