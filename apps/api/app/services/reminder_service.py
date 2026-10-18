import logging
from dataclasses import dataclass
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
from app.models.user_settings import UserSettings
from app.repositories.notification_repository import (
    NotificationRepository,
    PushSubscriptionRepository,
)
from app.services.gamification_service import GamificationService
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
) -> Message | None:
    if studied_today:
        return None

    key = local.date().isoformat()

    if streak_days > 0:
        return Message(
            TYPE_DAILY,
            f"Keep your {streak_days}-day streak alive",
            "One lesson today keeps it going. Finish today's quest.",
            "/learning",
            key,
        )

    return Message(
        TYPE_DAILY,
        "Time to study",
        "Start a lesson today and begin a new streak.",
        "/learning",
        key,
    )


def weekly_message(weekly_xp: int, local: datetime) -> Message | None:
    if local.weekday() != 0:
        return None

    year, week, _ = local.isocalendar()

    if weekly_xp > 0:
        body = f"You earned {weekly_xp} XP last week. Let's beat it."
    else:
        body = "A fresh week starts now. Pick up where you left off."

    return Message(
        TYPE_WEEKLY,
        "Your weekly summary",
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
                ),
                weekly_message(
                    await self.gamification.weekly_xp(profile), local
                ),
            ]

            for message in filter(None, messages):
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

        await self.db.commit()

        return {"notifications": sent, "pushes": pushed}
