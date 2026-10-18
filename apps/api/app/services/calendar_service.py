import secrets
from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
from app.models.user_settings import UserSettings
from app.repositories.profile_repository import ProfileRepository
from app.repositories.roadmap_repository import RoadmapRepository
from app.schemas.calendar import (
    CalendarScheduleResponse,
    ScheduledDay,
    ScheduledUnit,
)
from app.schemas.learning import LearningAgendaDayResponse
from app.services.gamification_service import local_today
from app.services.learning_service import get_learning_agenda

DEFAULT_REMINDER = time(9, 0)
MIN_EVENT_MINUTES = 30


def build_schedule(
    days: list[LearningAgendaDayResponse],
    start: date,
) -> list[ScheduledDay]:
    """Lays the unfinished study days out one per day from `start`.

    Finished days are skipped, so falling behind just shifts the plan
    forward instead of leaving missed days on the calendar.
    """
    remaining = [
        day for day in days if any(not u.completed for u in day.units)
    ]

    return [
        ScheduledDay(
            date=start + timedelta(days=offset),
            day=day.day,
            total_estimated_minutes=day.total_estimated_minutes,
            units=[
                ScheduledUnit(
                    id=u.id,
                    task_id=u.task_id,
                    task_title=u.task_title,
                    title=u.title,
                    type=u.type,
                    estimated_minutes=u.estimated_minutes,
                    completed=u.completed,
                )
                for u in day.units
            ],
        )
        for offset, day in enumerate(remaining)
    ]


def _escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def _fold(line: str) -> list[str]:
    """Folds a content line to 75 octets, as RFC 5545 requires."""
    encoded = line.encode("utf-8")

    if len(encoded) <= 75:
        return [line]

    parts: list[str] = []
    current = b""
    limit = 75

    for char in line:
        piece = char.encode("utf-8")
        if len(current) + len(piece) > limit:
            parts.append(current.decode("utf-8"))
            current = b""
            limit = 74  # continuation lines start with a space
        current += piece

    parts.append(current.decode("utf-8"))

    return [parts[0]] + [" " + part for part in parts[1:]]


def build_ics(
    schedule: list[ScheduledDay],
    roadmap_id: UUID | None,
    roadmap_title: str | None,
    reminder_time: time,
    now: datetime | None = None,
) -> str:
    """An iCalendar feed with one event per study day, at the user's
    reminder time (floating local time, so it follows their clock)."""
    now = now or datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Uraan AI//Learning plan//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape('Uraan AI learning plan')}",
        "X-PUBLISHED-TTL:PT6H",
    ]

    for day in schedule:
        start = datetime.combine(day.date, reminder_time)
        minutes = max(day.total_estimated_minutes, MIN_EVENT_MINUTES)
        end = start + timedelta(minutes=minutes)

        # Stable per study day, so calendars update events as the plan
        # shifts instead of duplicating them.
        uid = f"{roadmap_id}-{day.units[0].id}@uraan-ai"

        description = "\n".join(
            f"- {u.title} ({u.estimated_minutes or '?'} min)"
            for u in day.units
        )

        summary = f"Study: {day.units[0].task_title}"

        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{stamp}",
            f"DTSTART:{start.strftime('%Y%m%dT%H%M%S')}",
            f"DTEND:{end.strftime('%Y%m%dT%H%M%S')}",
            f"SUMMARY:{_escape(summary)}",
            f"DESCRIPTION:{_escape(description)}",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")

    folded = [part for line in lines for part in _fold(line)]

    return "\r\n".join(folded) + "\r\n"


class CalendarService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_repository = ProfileRepository(db)
        self.roadmap_repository = RoadmapRepository(db)

    async def _profile(self, auth_user_id: UUID) -> Profile:
        profile = await self.profile_repository.get_by_auth_user_id(
            auth_user_id
        )

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        return profile

    async def _settings(self, profile_id: UUID) -> UserSettings | None:
        result = await self.db.execute(
            select(UserSettings).where(UserSettings.profile_id == profile_id)
        )

        return result.scalar_one_or_none()

    async def _schedule_for(self, profile: Profile, settings):
        timezone_name = settings.timezone if settings else profile.timezone
        today = local_today(timezone_name)

        roadmap = await self.roadmap_repository.get_latest(profile.id)

        if roadmap is None:
            return None, [], today

        agenda = await get_learning_agenda(
            db=self.db,
            user_id=profile.auth_user_id,
            roadmap_id=roadmap.id,
            view="all",
        )

        return roadmap, build_schedule(agenda.days, today), today

    async def schedule(self, auth_user_id: UUID) -> CalendarScheduleResponse:
        profile = await self._profile(auth_user_id)
        settings = await self._settings(profile.id)

        roadmap, days, today = await self._schedule_for(profile, settings)

        return CalendarScheduleResponse(
            roadmap_id=roadmap.id if roadmap else None,
            roadmap_title=roadmap.title if roadmap else None,
            today=today,
            days=days,
        )

    async def token(self, auth_user_id: UUID, regenerate: bool = False) -> str:
        profile = await self._profile(auth_user_id)

        if profile.calendar_token and not regenerate:
            return profile.calendar_token

        try:
            profile.calendar_token = secrets.token_urlsafe(32)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        return profile.calendar_token

    async def feed(self, token: str) -> str:
        result = await self.db.execute(
            select(Profile).where(Profile.calendar_token == token)
        )
        profile = result.scalar_one_or_none()

        # Same answer for a wrong or revoked token.
        if profile is None:
            raise HTTPException(status_code=404, detail="Calendar not found")

        settings = await self._settings(profile.id)
        roadmap, days, _ = await self._schedule_for(profile, settings)

        return build_ics(
            days,
            roadmap.id if roadmap else None,
            roadmap.title if roadmap else None,
            settings.reminder_time if settings else DEFAULT_REMINDER,
        )
