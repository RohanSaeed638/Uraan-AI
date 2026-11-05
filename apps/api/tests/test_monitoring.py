"""Sentry and PostHog: off unless configured, careful with what they send, and
never a reason for a request to fail."""
import pytest

from app.core import analytics, monitoring
from app.core.config import settings


# ---- Sentry ---------------------------------------------------------------------------------------------------------------


def test_sentry_does_nothing_without_a_dsn(monkeypatch):
    monkeypatch.setattr(settings, "SENTRY_DSN", "")

    assert monitoring.init_sentry() is False


def test_sentry_starts_with_a_dsn_and_without_personal_data(monkeypatch):
    import sentry_sdk

    seen = {}
    monkeypatch.setattr(sentry_sdk, "init", lambda **kwargs: seen.update(kwargs))
    monkeypatch.setattr(settings, "SENTRY_DSN", "https://key@o0.ingest.sentry.io/1")

    assert monitoring.init_sentry() is True
    assert seen["send_default_pii"] is False and seen["before_send"] is monitoring.scrub
    assert seen["traces_sample_rate"] == settings.SENTRY_TRACES_SAMPLE_RATE


def test_a_sentry_failure_to_start_does_not_stop_the_api(monkeypatch):
    import sentry_sdk

    def boom(**kwargs):
        raise RuntimeError("bad dsn")

    monkeypatch.setattr(sentry_sdk, "init", boom)
    monkeypatch.setattr(settings, "SENTRY_DSN", "nonsense")

    assert monitoring.init_sentry() is False


def test_reports_leave_out_tokens_cookies_bodies_and_emails():
    event = {
        "request": {
            "url": "https://api/x",
            "headers": {"Authorization": "Bearer secret", "Cookie": "sb=1", "Accept": "*/*", "X-Api-Key": "k"},
            "cookies": {"sb": "1"},
            "data": {"password": "hunter2"},
            "query_string": "token=abc",
        },
        "user": {"id": "profile-1", "email": "a@b.com", "ip_address": "1.2.3.4", "username": "ayesha"},
    }

    clean = monitoring.scrub(event)

    assert clean["request"]["headers"] == {"Accept": "*/*"}
    assert not {"cookies", "data", "query_string"} & set(clean["request"])
    assert clean["user"] == {"id": "profile-1"}
    assert "hunter2" not in str(clean) and "secret" not in str(clean) and "a@b.com" not in str(clean)


def test_scrubbing_copes_with_odd_events():
    assert monitoring.scrub({}) == {}
    assert monitoring.scrub({"request": {"headers": None}, "user": None}) == {"request": {"headers": None}, "user": None}
    assert monitoring.scrub({"user": {"email": "a@b.com"}})["user"] == {}


def test_the_helpers_never_raise_without_sentry():
    monitoring.tag_request("abc12345")
    monitoring.identify("profile-1")
    monitoring.report(RuntimeError("x"))


# ---- PostHog --------------------------------------------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def fresh_analytics():
    analytics.reset_for_tests()
    yield
    analytics.reset_for_tests()


def test_analytics_do_nothing_without_a_key(monkeypatch):
    monkeypatch.setattr(settings, "POSTHOG_API_KEY", "")

    analytics.track("profile-1", "lesson_completed")
    analytics.flush()

    assert analytics._posthog() is None


def test_an_event_carries_the_profile_id_and_properties_only(monkeypatch):
    sent = []

    class Fake:
        def capture(self, event, **kwargs):
            sent.append((event, kwargs))

    monkeypatch.setattr(settings, "POSTHOG_API_KEY", "phc_test")
    monkeypatch.setattr(analytics, "_client", Fake())
    monkeypatch.setattr(analytics, "_started", True)

    analytics.track("0192-abc", "xp_earned", reason="lesson", amount=10)

    event, kwargs = sent[0]

    assert event == "xp_earned" and kwargs["distinct_id"] == "0192-abc"
    assert kwargs["properties"]["reason"] == "lesson" and kwargs["properties"]["amount"] == 10
    assert set(kwargs) == {"distinct_id", "properties"}


def test_no_profile_means_no_event(monkeypatch):
    sent = []

    class Fake:
        def capture(self, *args, **kwargs):
            sent.append(1)

    monkeypatch.setattr(analytics, "_client", Fake())
    monkeypatch.setattr(analytics, "_started", True)

    analytics.track(None, "x")

    assert sent == []


def test_a_failing_analytics_service_never_reaches_the_learner(monkeypatch):
    class Broken:
        def capture(self, *args, **kwargs):
            raise ConnectionError("posthog is down")

        def flush(self):
            raise ConnectionError("posthog is down")

    monkeypatch.setattr(analytics, "_client", Broken())
    monkeypatch.setattr(analytics, "_started", True)

    analytics.track("p", "x")
    analytics.flush()


def test_a_bad_key_does_not_stop_the_api(monkeypatch):
    import posthog

    monkeypatch.setattr(settings, "POSTHOG_API_KEY", "phc_test")

    def boom(*args, **kwargs):
        raise RuntimeError("cannot start")

    monkeypatch.setattr(posthog, "Posthog", boom)

    assert analytics._posthog() is None
    analytics.track("p", "x")


def test_xp_awards_are_tracked_as_events(monkeypatch):
    """Every way of earning XP is one event, so the KPIs need no per-feature code."""
    import asyncio
    from types import SimpleNamespace
    from uuid import uuid4

    from app.services import gamification_service as gs

    tracked = []
    monkeypatch.setattr(gs, "track", lambda pid, event, **props: tracked.append((pid, event, props)))

    class Result:
        def scalar_one_or_none(self):
            return uuid4()

    class Db:
        async def execute(self, stmt):
            return Result()

        async def flush(self):
            pass

    monkeypatch.undo()  # the autouse fake in conftest replaces award itself; use the real one
    monkeypatch.setattr(gs, "track", lambda pid, event, **props: tracked.append((pid, event, props)))

    profile = SimpleNamespace(id=uuid4(), xp=0, streak_days=0, last_activity_date=None, timezone="UTC")

    asyncio.run(gs.GamificationService(Db()).award(profile, 10, "lesson", uuid4(), evaluate=False))

    assert tracked and tracked[0][1] == "xp_earned" and tracked[0][2] == {"reason": "lesson", "amount": 10}
