import logging
from dataclasses import dataclass
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.texts import text
from app.models.profile import Profile
from app.models.user_settings import UserSettings
from app.repositories.notification_repository import (
    NotificationRepository,
    PushSubscriptionRepository,
)
from app.services.email_service import EmailService
from app.services.gamification_service import GamificationService
from app.services.motivation_service import MotivationService
from app.services.push_service import send_push

logger = logging.getLogger(__name__)

# A user is "due" for this long after their reminder time. Each reminder is
# deduplicated per day, so a late or repeated run still sends at most one.
WINDOW_MINUTES = 30

TYPE_DAILY = "daily_reminder"
TYPE_WEEKLY = "weekly_summary"


def local_now(tz_name: str | None, now: datetime) -> datetime:
    try:
        tz = ZoneInfo(tz_name) if tz_name else timezone.utc
    except ZoneInfoNotFoundError:
        tz = timezone.utc

    return now.astimezone(tz)


def is_due(
    now: datetime,
    reminder_time: time,
    tz_name: str | None,
    window_minutes: int = WINDOW_MINUTES,
) -> bool:
    """Whether `now` is within the window after the reminder time,
    measured on the user's own clock (including across midnight)."""
    local = local_now(tz_name, now)

    now_minutes = local.hour * 60 + local.minute
    reminder_minutes = reminder_time.hour * 60 + reminder_time.minute

    return (now_minutes - reminder_minutes) % 1440 < window_minutes


@dataclass
class Message:
    type: str
    title: str
    body: str
    url: str
    dedupe_key: str


def daily_message(
    streak_days: int,
    studied_today: bool,
    local: datetime,
    language: str | None = None,
) -> Message | None:
    if studied_today:
        return None

    key = local.date().isoformat()

    if streak_days > 0:
        return Message(
            TYPE_DAILY,
            text("daily_streak_title", language, days=streak_days),
            text("daily_streak_body", language),
            "/learning",
            key,
        )

    return Message(
        TYPE_DAILY,
        text("daily_start_title", language),
        text("daily_start_body", language),
        "/learning",
        key,
    )


def weekly_message(weekly_xp: int, local: datetime, language: str | None = None) -> Message | None:
    if local.weekday() != 0:
        return None

    year, week, _ = local.isocalendar()

    if weekly_xp > 0:
        body = text("weekly_xp", language, xp=weekly_xp)
    else:
        body = text("weekly_fresh", language)

    return Message(
        TYPE_WEEKLY,
        text("weekly_title", language),
        body,
        "/progress",
        f"{year}-W{week:02d}",
    )


class ReminderService:
    """Creates due reminders and pushes them. Meant to run on a schedule."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.notifications = NotificationRepository(db)
        self.subscriptions = PushSubscriptionRepository(db)
        self.gamification = GamificationService(db)
        self.emails = EmailService(db)

    async def _motivation(self, profile, settings) -> str | None:
        """Today's motivational message to use as the reminder text. Never
        stops a reminder from going out."""
        try:
            return (await MotivationService(self.db).for_profile(profile, settings))["message"]
        except Exception:
            # No rollback here: it would also undo the reminders already
            # created earlier in this run.
            logger.exception("Could not get today's motivation for a reminder")

            return None

    async def _roll_over(self, now: datetime) -> int:
        """Once a day for every learner (reminders on or off): lessons they
        missed and did not pin are planned again, and they are told. Runs
        after the day has properly started on their clock."""
        from app.services.calendar_service import CalendarService

        rows = (
            await self.db.execute(
                select(Profile, UserSettings).outerjoin(
                    UserSettings, UserSettings.profile_id == Profile.id
                )
            )
        ).all()

        service = CalendarService(self.db)
        total = 0

        for profile, settings in rows:
            tz = settings.timezone if settings else profile.timezone

            # Not before 04:00 local: late-night study still counts as today.
            if local_now(tz, now).hour < 4:
                continue

            try:
                total += await service.roll_over(profile, settings)
            except Exception:
                # No rollback: it would undo the reminders created earlier in this run.
                logger.exception("Schedule roll-over failed for %s", profile.id)

        return total

    async def run(self, now: datetime | None = None) -> dict:
        now = now or datetime.now(timezone.utc)

        rows = (
            await self.db.execute(
                select(Profile, UserSettings)
                .join(UserSettings, UserSettings.profile_id == Profile.id)
                .where(UserSettings.learning_reminders.is_(True))
            )
        ).all()

        sent = 0
        pushed = 0

        for profile, settings in rows:
            if not is_due(now, settings.reminder_time, settings.timezone):
                continue

            local = local_now(settings.timezone, now)

            messages = [
                daily_message(
                    profile.streak_days or 0,
                    profile.last_activity_date == local.date(),
                    local,
                    profile.language,
                ),
                weekly_message(
                    await self.gamification.weekly_xp(profile), local, profile.language
                ),
            ]

            for message in filter(None, messages):
                if message.type == TYPE_DAILY:
                    message.body = await self._motivation(profile, settings) or message.body

                created = await self.notifications.create_once(
                    profile_id=profile.id,
                    type=message.type,
                    title=message.title,
                    body=message.body,
                    url=message.url,
                    dedupe_key=message.dedupe_key,
                )

                if created is None:
                    continue

                sent += 1

                await self.emails.notify(profile, message.type, message.title, message.body, message.url)

                subscriptions = await self.subscriptions.list_for_profile(
                    profile.id
                )
                pushed += await send_push(
                    self.subscriptions,
                    subscriptions,
                    message.title,
                    message.body,
                    message.url,
                )

        moved = await self._roll_over(now)

        await self.db.commit()

        return {"notifications": sent, "pushes": pushed, "moved": moved}
