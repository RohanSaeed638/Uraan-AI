"""Web push delivery, and the reminder job that runs every 15 minutes."""
import asyncio
import selectors
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pywebpush import WebPushException

from app.core.config import settings
from app.services import push_service
from app.workers import send_reminders


def run(coro):
    return asyncio.run(coro, loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))


def sub(name):
    return SimpleNamespace(endpoint=f"https://push.example/{name}", p256dh="k", auth="a")


class Repo:
    def __init__(self):
        self.deleted = []

    async def delete_by_endpoint(self, endpoint):
        self.deleted.append(endpoint)


@pytest.fixture
def push_on(monkeypatch):
    monkeypatch.setattr(settings, "VAPID_PUBLIC_KEY", "pub")
    monkeypatch.setattr(settings, "VAPID_PRIVATE_KEY", "priv")


def failing(status):
    return WebPushException("push failed", response=SimpleNamespace(status_code=status))


def sender(monkeypatch, outcomes):
    """Replaces the network call: each subscription gets the outcome named for its endpoint."""
    sent = []

    def fake(subscription, payload):
        sent.append((subscription.endpoint, payload))
        outcome = outcomes.get(subscription.endpoint)

        if outcome:
            raise outcome

    monkeypatch.setattr(push_service, "_send_sync", fake)
    return sent


def test_push_is_off_without_keys(monkeypatch):
    monkeypatch.setattr(settings, "VAPID_PUBLIC_KEY", "")
    monkeypatch.setattr(settings, "VAPID_PRIVATE_KEY", "")
    sent = sender(monkeypatch, {})

    assert push_service.push_enabled() is False
    assert run(push_service.send_push(Repo(), [sub("a")], "t", "b", None)) == 0
    assert sent == []


def test_it_needs_both_keys(monkeypatch):
    monkeypatch.setattr(settings, "VAPID_PUBLIC_KEY", "pub")
    monkeypatch.setattr(settings, "VAPID_PRIVATE_KEY", "")

    assert push_service.push_enabled() is False


def test_every_device_is_sent_the_message_and_counted(push_on, monkeypatch):
    sent = sender(monkeypatch, {})
    delivered = run(push_service.send_push(Repo(), [sub("a"), sub("b")], "Time to learn", "Day 3", "/roadmaps/1"))

    assert delivered == 2
    assert sent[0][1] == {"title": "Time to learn", "body": "Day 3", "url": "/roadmaps/1"}


def test_a_message_with_no_link_opens_the_dashboard(push_on, monkeypatch):
    sent = sender(monkeypatch, {})
    run(push_service.send_push(Repo(), [sub("a")], "t", "b", None))

    assert sent[0][1]["url"] == "/dashboard"


@pytest.mark.parametrize("status", [404, 410])
def test_a_device_the_push_service_says_is_gone_is_forgotten(push_on, monkeypatch, status):
    repo = Repo()
    sender(monkeypatch, {"https://push.example/old": failing(status)})
    delivered = run(push_service.send_push(repo, [sub("old"), sub("new")], "t", "b", None))

    assert delivered == 1 and repo.deleted == ["https://push.example/old"]


def test_other_failures_keep_the_device_and_never_stop_the_rest(push_on, monkeypatch):
    repo = Repo()
    sender(
        monkeypatch,
        {"https://push.example/slow": failing(500), "https://push.example/odd": RuntimeError("boom")},
    )
    delivered = run(push_service.send_push(repo, [sub("slow"), sub("odd"), sub("fine")], "t", "b", None))

    assert delivered == 1 and repo.deleted == []


# ---- the reminder job -----------------------------------------------------------------------------------------------------------


class FakeSession:
    def __init__(self):
        self.rolled_back = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def rollback(self):
        self.rolled_back = True


def job(monkeypatch, result=None, error=None):
    session = FakeSession()
    waited = []

    class Reminders:
        def __init__(self, db):
            pass

        async def run(self):
            if error:
                raise error

            return result

    async def wait():
        waited.append(True)

    monkeypatch.setattr(send_reminders, "SessionLocal", lambda: session)
    monkeypatch.setattr(send_reminders, "ReminderService", Reminders)
    monkeypatch.setattr(send_reminders, "wait_for_pending", wait)
    return session, waited


def test_the_job_runs_the_reminders_and_waits_for_emails_to_finish(monkeypatch):
    session, waited = job(monkeypatch, result={"sent": 3})
    run(send_reminders.main())

    assert waited == [True] and session.rolled_back is False


def test_a_failing_job_rolls_back_and_fails_loudly_so_the_scheduler_notices(monkeypatch):
    session, waited = job(monkeypatch, error=RuntimeError("database down"))

    with pytest.raises(RuntimeError):
        run(send_reminders.main())

    assert session.rolled_back is True and waited == []
