"""Email for learners: the templates, the senders (Resend, or files in dev) and
the rules for who gets what.

An email goes out only when all of these hold: the notification is one of the
types worth emailing, the learner has email notifications on, the server has a
sender configured and the learner has an address. It never raises into the
request or job that created the notification, and it never blocks it: the send
runs in the background.
"""
import asyncio
import html
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol
from uuid import UUID, uuid4

import httpx
from sqlalchemy import text as sql
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.email_token import make_token
from app.core.texts import text
from app.models.user_settings import UserSettings

logger = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"

# Notification types that are also sent by email: reminders and summaries, and
# the moments worth celebrating. Schedule changes stay in the app.
EMAIL_TYPES = {"daily_reminder", "weekly_summary", "achievement", "boss_defeated", "streak"}

# Kept so a background send is not garbage collected before it finishes.
_pending: set[asyncio.Task] = set()


class Sender(Protocol):
    async def send(self, to: str, subject: str, html_body: str, text_body: str, headers: dict) -> None: ...


class ResendSender:
    """https://resend.com/docs/api-reference/emails/send-email"""

    def __init__(self, api_key: str, sender: str, transport: httpx.AsyncBaseTransport | None = None):
        self.api_key = api_key
        self.sender = sender
        self.transport = transport

    async def send(self, to, subject, html_body, text_body, headers):
        async with httpx.AsyncClient(timeout=15, transport=self.transport) as client:
            response = await client.post(
                RESEND_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "from": self.sender,
                    "to": [to],
                    "subject": subject,
                    "html": html_body,
                    "text": text_body,
                    "headers": headers,
                },
            )

        if response.status_code >= 400:
            # The body says why (unverified domain, bad address...) and holds no secrets.
            raise RuntimeError(f"Resend answered {response.status_code}: {response.text[:300]}")


class OutboxSender:
    """Development: writes each email to a JSON file instead of sending it."""

    def __init__(self, folder: str):
        self.folder = Path(folder)

    async def send(self, to, subject, html_body, text_body, headers):
        self.folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        payload = {"to": to, "subject": subject, "html": html_body, "text": text_body, "headers": headers}

        (self.folder / f"{stamp}-{uuid4().hex[:8]}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def configured_sender() -> Sender | None:
    if settings.RESEND_API_KEY:
        return ResendSender(settings.RESEND_API_KEY, settings.EMAIL_FROM)

    if settings.EMAIL_OUTBOX_DIR:
        return OutboxSender(settings.EMAIL_OUTBOX_DIR)

    return None


def email_available() -> bool:
    return configured_sender() is not None


# ---- the message ----------------------------------------------------------------------------------------------


def unsubscribe_links(profile_id: UUID) -> tuple[str, str]:
    """(the page a person opens, the address mail apps call for one-click unsubscribe)"""
    token = make_token(profile_id)

    return (
        f"{settings.WEB_URL.rstrip('/')}/unsubscribe?token={token}",
        f"{settings.API_PUBLIC_URL.rstrip('/')}/email/unsubscribe?token={token}",
    )


def absolute(url: str | None) -> str:
    if not url:
        return settings.WEB_URL.rstrip("/") + "/dashboard"

    return url if url.startswith("http") else settings.WEB_URL.rstrip("/") + url


def render(title: str, body: str, url: str | None, language: str | None, profile_id: UUID) -> dict:
    """Subject, HTML, plain text and headers for one notification."""
    open_url = absolute(url)
    unsubscribe_page, unsubscribe_post = unsubscribe_links(profile_id)
    rtl = language == "ur"
    t = lambda key: text(key, language)  # noqa: E731
    e = html.escape

    page = f"""<!doctype html>
<html lang="{e(language or 'en')}" dir="{'rtl' if rtl else 'ltr'}">
<body style="margin:0;background:#f4f1ea;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#1c1830">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="padding:24px 12px">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
             style="max-width:520px;background:#ffffff;border-radius:20px;overflow:hidden">
        <tr><td style="background:#f5a83c;padding:18px 28px;font-size:18px;font-weight:700;color:#241a05">Uraan AI</td></tr>
        <tr><td style="padding:28px">
          <h1 style="margin:0 0 12px;font-size:20px;line-height:1.35">{e(title)}</h1>
          <p style="margin:0 0 24px;font-size:15px;line-height:1.65;color:#3b3654">{e(body)}</p>
          <a href="{e(open_url)}" style="display:inline-block;background:#f5a83c;color:#241a05;text-decoration:none;
             font-weight:600;padding:12px 22px;border-radius:999px">{e(t('email_open'))}</a>
        </td></tr>
        <tr><td style="padding:18px 28px;border-top:1px solid #ece8f5;font-size:12px;line-height:1.6;color:#7a7596">
          {e(t('email_reason'))}<br>
          <a href="{e(unsubscribe_page)}" style="color:#b45f06">{e(t('email_unsubscribe'))}</a>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    plain = "\n\n".join(
        [title, body, f"{t('email_open')}: {open_url}", f"{t('email_reason')}\n{t('email_unsubscribe')}: {unsubscribe_page}"]
    )

    return {
        "subject": re.sub(r"\s+", " ", title).strip(),
        "html": page,
        "text": plain,
        "headers": {
            # One-click unsubscribe (RFC 8058): mail apps show their own button.
            "List-Unsubscribe": f"<{unsubscribe_post}>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        },
    }


# ---- who gets what ------------------------------------------------------------------------------------------


class EmailService:
    def __init__(self, db: AsyncSession, sender: Sender | None = None):
        self.db = db
        self.sender = sender if sender is not None else configured_sender()

    async def address(self, profile) -> str | None:
        """The learner's login email. It lives in Supabase's auth schema, which
        the API's database role can read."""
        row = (
            await self.db.execute(
                sql("select email from auth.users where id = :id"), {"id": profile.auth_user_id}
            )
        ).first()

        return row[0] if row and row[0] else None

    async def wants_email(self, profile) -> bool:
        from sqlalchemy import select

        enabled = (
            await self.db.execute(
                select(UserSettings.email_notifications).where(UserSettings.profile_id == profile.id)
            )
        ).scalar_one_or_none()

        # No settings row yet means the defaults, which are on.
        return True if enabled is None else bool(enabled)

    async def notify(self, profile, type: str, title: str, body: str, url: str | None) -> bool:
        """Emails a notification that was just created, if the rules allow.
        Returns whether an email was started."""
        if self.sender is None or type not in EMAIL_TYPES:
            return False

        try:
            if not await self.wants_email(profile):
                return False

            to = await self.address(profile)

            if not to:
                return False

            message = render(title, body, url, getattr(profile, "language", None), profile.id)
        except Exception:
            logger.exception("Could not prepare an email for %s", profile.id)

            return False

        task = asyncio.ensure_future(self._deliver(to, message))
        _pending.add(task)
        task.add_done_callback(_pending.discard)

        return True

    async def _deliver(self, to: str, message: dict) -> None:
        try:
            await self.sender.send(to, message["subject"], message["html"], message["text"], message["headers"])
        except Exception:
            logger.exception("Email to a learner failed")


async def wait_for_pending() -> None:
    """For jobs and tests: lets background sends finish before the process ends."""
    if _pending:
        await asyncio.gather(*list(_pending), return_exceptions=True)
