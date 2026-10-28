"""Email: signed unsubscribe links, the message, the senders and who gets what."""
import asyncio
import json
import selectors
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.api.routes.email import router as email_router
from app.core.config import settings
from app.core.email_token import make_token, read_token
from app.db.base import get_db
from app.models.profile import Profile
from app.models.user_settings import UserSettings
from app.services.email_service import (
    EMAIL_TYPES,
    EmailService,
    OutboxSender,
    ResendSender,
    configured_sender,
    email_available,
    render,
    wait_for_pending,
)

PID = uuid4()


# ---- the signed link ------------------------------------------------------------------------------------------


def test_a_token_gives_back_the_profile():
    assert read_token(make_token(PID)) == PID


def test_a_tampered_or_foreign_token_is_refused():
    token = make_token(PID)
    body, signature = token.split(".")

    assert read_token(body + "." + signature[:-2] + "xx") is None
    assert read_token(make_token(uuid4()).split(".")[0] + "." + signature) is None  # another person's body
    assert read_token("nonsense") is None
    assert read_token("") is None
    assert read_token(make_token(PID, "something-else")) is None  # another purpose


def test_tokens_are_not_the_bare_profile_id():
    assert str(PID) not in make_token(PID)


# ---- the message ----------------------------------------------------------------------------------------------


def test_the_email_has_the_text_the_link_and_a_one_click_unsubscribe():
    mail = render("Keep your 5-day streak alive", "One lesson today keeps it going.", "/learning", "en", PID)

    assert mail["subject"] == "Keep your 5-day streak alive"
    assert "One lesson today keeps it going." in mail["html"] and "One lesson today" in mail["text"]
    assert f"{settings.WEB_URL}/learning" in mail["html"]
    assert "/unsubscribe?token=" in mail["html"] and "/unsubscribe?token=" in mail["text"]
    assert mail["headers"]["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
    assert mail["headers"]["List-Unsubscribe"].startswith(f"<{settings.API_PUBLIC_URL}/email/unsubscribe?token=")

    token = mail["headers"]["List-Unsubscribe"].split("token=")[1].rstrip(">")

    assert read_token(token) == PID


def test_what_a_learner_wrote_cannot_inject_html():
    mail = render('<script>alert(1)</script>', 'a "quote" & <b>bold</b>', None, "en", PID)

    assert "<script>" not in mail["html"] and "&lt;script&gt;" in mail["html"]
    assert "<b>bold</b>" not in mail["html"]


def test_urdu_goes_right_to_left_and_roman_urdu_does_not():
    assert 'dir="rtl"' in render("t", "b", None, "ur", PID)["html"]
    assert 'dir="ltr"' in render("t", "b", None, "ur-Latn", PID)["html"]
    assert 'dir="ltr"' in render("t", "b", None, None, PID)["html"]
    assert "ان سبسکرائب" in render("t", "b", None, "ur", PID)["html"]
    assert "Unsubscribe karein" in render("t", "b", None, "ur-Latn", PID)["html"]


def test_no_url_opens_the_dashboard():
    assert render("t", "b", None, "en", PID)["html"].count(f"{settings.WEB_URL}/dashboard") == 1


# ---- the senders ----------------------------------------------------------------------------------------------


def run(coro):
    return asyncio.run(coro, loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))


def test_resend_gets_the_right_request():
    seen = {}

    def handler(request: httpx.Request):
        seen["auth"] = request.headers["authorization"]
        seen["url"] = str(request.url)
        seen["json"] = json.loads(request.content)

        return httpx.Response(200, json={"id": "abc"})

    sender = ResendSender("re_key", "Uraan AI <hi@example.com>", httpx.MockTransport(handler))

    run(sender.send("a@b.com", "Hello", "<p>x</p>", "x", {"List-Unsubscribe": "<u>"}))

    assert seen["auth"] == "Bearer re_key" and seen["url"] == "https://api.resend.com/emails"
    assert seen["json"] == {
        "from": "Uraan AI <hi@example.com>",
        "to": ["a@b.com"],
        "subject": "Hello",
        "html": "<p>x</p>",
        "text": "x",
        "headers": {"List-Unsubscribe": "<u>"},
    }


def test_resend_errors_are_raised_without_the_key():
    sender = ResendSender(
        "re_secret", "x", httpx.MockTransport(lambda r: httpx.Response(403, json={"message": "domain not verified"}))
    )

    with pytest.raises(RuntimeError) as error:
        run(sender.send("a@b.com", "s", "h", "t", {}))

    assert "403" in str(error.value) and "domain not verified" in str(error.value)
    assert "re_secret" not in str(error.value)


def test_the_dev_outbox_writes_a_file(tmp_path):
    run(OutboxSender(str(tmp_path / "mail")).send("a@b.com", "Hi", "<p>h</p>", "h", {"X": "1"}))

    files = list((tmp_path / "mail").glob("*.json"))
    saved = json.loads(files[0].read_text(encoding="utf-8"))

    assert len(files) == 1 and saved["to"] == "a@b.com" and saved["subject"] == "Hi"


def test_the_configured_sender(monkeypatch):
    monkeypatch.setattr(settings, "RESEND_API_KEY", "")
    monkeypatch.setattr(settings, "EMAIL_OUTBOX_DIR", "")

    assert configured_sender() is None and email_available() is False

    monkeypatch.setattr(settings, "EMAIL_OUTBOX_DIR", "x")

    assert isinstance(configured_sender(), OutboxSender) and email_available() is True

    monkeypatch.setattr(settings, "RESEND_API_KEY", "k")

    assert isinstance(configured_sender(), ResendSender)  # a real key wins over the dev folder


# ---- who gets what --------------------------------------------------------------------------------------------


class Recorder:
    def __init__(self, fail=False):
        self.sent = []
        self.fail = fail

    async def send(self, to, subject, html, text_body, headers):
        if self.fail:
            raise RuntimeError("provider down")

        self.sent.append((to, subject))


class Service(EmailService):
    """The rules, without a database."""

    def __init__(self, sender, enabled=True, address="ayesha@example.com"):
        self.sender, self.enabled, self.to = sender, enabled, address

    async def wants_email(self, profile):
        return self.enabled

    async def address(self, profile):
        return self.to


PROFILE = SimpleNamespace(id=PID, language="en", auth_user_id=uuid4())


def notify(service, type="daily_reminder"):
    async def go():
        started = await service.notify(PROFILE, type, "Time to study", "Start a lesson.", "/learning")
        await wait_for_pending()

        return started

    return run(go())


def test_an_email_goes_to_a_learner_who_wants_it():
    sender = Recorder()

    assert notify(Service(sender)) is True
    assert sender.sent == [("ayesha@example.com", "Time to study")]


@pytest.mark.parametrize("type", sorted(EMAIL_TYPES))
def test_every_celebration_and_reminder_type_is_emailed(type):
    sender = Recorder()

    assert notify(Service(sender), type) is True and len(sender.sent) == 1


def test_schedule_updates_and_unknown_types_stay_in_the_app():
    sender = Recorder()

    assert notify(Service(sender), "schedule_updated") is False
    assert notify(Service(sender), "who-knows") is False
    assert sender.sent == []


def test_nothing_is_sent_when_the_learner_turned_email_off():
    sender = Recorder()

    assert notify(Service(sender, enabled=False)) is False and sender.sent == []


def test_nothing_is_sent_without_an_address_or_a_sender():
    sender = Recorder()

    assert notify(Service(sender, address=None)) is False and sender.sent == []
    assert notify(Service(None)) is False


def test_a_failing_provider_never_breaks_the_caller():
    assert notify(Service(Recorder(fail=True))) is True  # started; the failure is only logged


def test_preparing_the_email_failing_never_breaks_the_caller():
    class Broken(Service):
        async def address(self, profile):
            raise RuntimeError("database gone")

    assert notify(Broken(Recorder())) is False


# ---- the database -----------------------------------------------------------------------------------------------


def with_db(fn):
    async def go():
        engine = create_async_engine(settings.DATABASE_URL)
        try:
            async with engine.connect() as conn:
                trans = await conn.begin()
                db = AsyncSession(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)
                try:
                    auth_id = uuid4()
                    await db.execute(
                        text(
                            "insert into auth.users (instance_id, id, aud, role, email) values "
                            "('00000000-0000-0000-0000-000000000000', :i, 'authenticated', 'authenticated', :e)"
                        ),
                        {"i": auth_id, "e": "test-address@example.com"},
                    )
                    me = Profile(auth_user_id=auth_id, full_name="Ayesha", daily_hours=1, xp=0, streak_days=0)
                    db.add(me)
                    await db.flush()

                    return await fn(db, me)
                finally:
                    await db.close()
                    await trans.rollback()
        finally:
            await engine.dispose()

    try:
        return run(go())
    except OSError as exc:
        pytest.skip(f"database not reachable: {type(exc).__name__}")


def test_the_address_comes_from_the_login_and_the_choice_from_settings():
    async def check(db, me):
        service = EmailService(db, sender=Recorder())

        assert await service.address(me) == "test-address@example.com"
        assert await service.wants_email(me) is True  # no settings row yet: the default

        db.add(UserSettings(profile_id=me.id, email_notifications=False))
        await db.flush()

        assert await service.wants_email(me) is False

    with_db(check)


def test_the_whole_path_sends_an_email_for_a_real_profile():
    async def check(db, me):
        sender = Recorder()
        service = EmailService(db, sender=sender)

        assert await service.notify(me, "weekly_summary", "Your weekly summary", "You earned 40 XP.", "/progress")
        await wait_for_pending()

        return sender.sent

    assert with_db(check) == [("test-address@example.com", "Your weekly summary")]


def test_unsubscribing_turns_email_off_and_is_repeatable():
    async def check(db, me):
        db.add(UserSettings(profile_id=me.id, email_notifications=True))
        await db.flush()

        api = FastAPI()
        api.include_router(email_router)
        api.dependency_overrides[get_db] = lambda: db
        token = make_token(me.id)

        async def call(method, url):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://t") as client:
                return await client.request(method, url)

        assert (await call("GET", f"/email/unsubscribe?token={token}")).json() == {"subscribed": True}
        # Opening the link (a mail scanner might) changes nothing.
        assert (await call("GET", f"/email/unsubscribe?token={token}")).json() == {"subscribed": True}

        first = await call("POST", f"/email/unsubscribe?token={token}")
        second = await call("POST", f"/email/unsubscribe?token={token}")

        assert first.json() == second.json() == {"subscribed": False}
        assert (await call("GET", f"/email/unsubscribe?token={token}")).json() == {"subscribed": False}

        bad = await call("POST", "/email/unsubscribe?token=" + token[:-3] + "abc")
        assert bad.status_code == 400 and bad.json()["detail"] == "This unsubscribe link is not valid."

        stranger = await call("POST", f"/email/unsubscribe?token={make_token(uuid4())}")
        assert stranger.status_code == 400  # a valid signature for someone with no settings

    with_db(check)


def test_the_reminder_run_emails_a_due_learner_once():
    from datetime import datetime, time, timezone

    from app.services.reminder_service import ReminderService

    async def check(db, me):
        me.timezone = "UTC"
        db.add(UserSettings(profile_id=me.id, learning_reminders=True, email_notifications=True,
                            reminder_time=time(9, 0), timezone="UTC"))
        await db.flush()

        sender = Recorder()
        service = ReminderService(db)
        service.emails = EmailService(db, sender=sender)
        now = datetime(2026, 11, 3, 9, 5, tzinfo=timezone.utc)  # a Tuesday, five minutes after

        await service.run(now)
        await service.run(now)  # a repeated run must not send it again
        await wait_for_pending()

        return [s for s in sender.sent if s[0] == "test-address@example.com"]

    sent = with_db(check)

    assert len(sent) == 1 and sent[0][1] == "Time to study"
