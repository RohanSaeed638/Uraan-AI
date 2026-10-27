"""The learner's study calendar: the plan (see planner.py), moving lessons,
the AI "optimise my schedule" helper, missed-lesson roll-over and the .ics feed."""
import logging
import secrets
from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm import AIUnavailableError, complete_text, use_profile
from app.core.texts import text as message, short_date
from app.ai.parser import parse_ai_json
from app.ai.prompts.planner_prompt import PLANNER_PROMPT
from app.ai.schemas.planner_schema import PlannerRules
from app.ai.versions import prompt_version
from app.models.ai_request import AiRequest
from app.models.planner import ScheduleOverride, SchedulePreference, ScheduleSnapshot
from app.models.profile import Profile
from app.models.user_settings import UserSettings
from app.repositories.learning_repository import get_roadmap_learning_units
from app.repositories.notification_repository import NotificationRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.roadmap_repository import RoadmapRepository
from app.services.gamification_service import local_today
from app.services.planner import (
    MAX_DAILY_MINUTES,
    PART_OF_DAY_START,
    Availability,
    PlanResult,
    PlanUnit,
    clamp_daily_minutes,
    plan,
    start_for,
)

logger = logging.getLogger(__name__)

DEFAULT_REMINDER = time(9, 0)
MIN_EVENT_MINUTES = 30

# How far ahead a lesson can be moved, and how many AI re-plans a day.
MOVE_HORIZON_DAYS = 365
OPTIMISE_DAILY_LIMIT = 10
WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

TYPE_SCHEDULE = "schedule_updated"


# ---- availability ----------------------------------------------------------------------------------


def availability_for(profile, settings, prefs, today: date | None = None) -> Availability:
    """When the learner can study: their daily hours and weekend choice from
    onboarding, adjusted by anything they told the planner."""
    daily = clamp_daily_minutes((profile.daily_hours or 2) * 60)
    minutes = [daily] * 7

    if getattr(profile, "weekend_study", None) is False:
        minutes[5] = minutes[6] = 0

    blocked: set[date] = set()
    start = None

    if prefs is not None:
        for key, value in (prefs.weekday_minutes or {}).items():
            try:
                index = int(key)
            except (TypeError, ValueError):
                continue

            if 0 <= index <= 6:
                minutes[index] = min(max(int(value), 0), MAX_DAILY_MINUTES)

        for raw in prefs.blocked_dates or []:
            try:
                blocked.add(date.fromisoformat(raw))
            except (TypeError, ValueError):
                continue

        start = prefs.start_time

    reminder = getattr(settings, "reminder_time", None)

    return Availability(
        weekday_minutes=minutes,
        blocked=blocked,
        start=start or start_for(getattr(profile, "preferred_study_hours", None), reminder),
    )


def serialise(result: PlanResult, today: date) -> list[dict]:
    """The plan as plain data for the API."""
    return [
        {
            "date": day.date,
            "start": day.start,
            "end": day.end,
            "minutes": day.minutes,
            "units": [
                {
                    "id": p.unit.id,
                    "task_id": p.unit.task_id,
                    "task_title": p.unit.task_title,
                    "title": p.unit.title,
                    "type": p.unit.type,
                    "minutes": p.unit.length,
                    "start": p.start,
                    "end": p.end,
                    "pinned": p.pinned,
                    "missed": p.missed,
                    "completed": False,
                }
                for p in day.placed
            ],
        }
        for day in result.days
    ]


# ---- the .ics feed ------------------------------------------------------------------------------------------


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
    days: list[dict],
    roadmap_id: UUID | None,
    now: datetime | None = None,
) -> str:
    """An iCalendar feed with one event per study day, at the day's planned
    time (floating local time, so it follows the learner's clock)."""
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

    for day in days:
        start = datetime.combine(day["date"], day["start"])
        end = max(datetime.combine(day["date"], day["end"]), start + timedelta(minutes=MIN_EVENT_MINUTES))

        # One stable id per study date, so calendars update that day's event
        # as the plan shifts instead of duplicating it.
        uid = f"{roadmap_id}-{day['date'].isoformat()}@uraan-ai"

        description = "\n".join(
            f"- {u['start'].strftime('%H:%M')} {u['title']} ({u['minutes']} min)"
            for u in day["units"]
        )

        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{stamp}",
            f"DTSTART:{start.strftime('%Y%m%dT%H%M%S')}",
            f"DTEND:{end.strftime('%Y%m%dT%H%M%S')}",
            f"SUMMARY:{_escape('Study: ' + day['units'][0]['task_title'])}",
            f"DESCRIPTION:{_escape(description)}",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")

    folded = [part for line in lines for part in _fold(line)]

    return "\r\n".join(folded) + "\r\n"


# ---- the service -----------------------------------------------------------------------------------------------------


class CalendarService:

    def __init__(self, db: AsyncSession, ask=None):
        self.db = db
        self.profile_repository = ProfileRepository(db)
        self.roadmap_repository = RoadmapRepository(db)
        self.notifications = NotificationRepository(db)
        self._ask = ask or complete_text

    async def _profile(self, auth_user_id: UUID) -> Profile:
        profile = await self.profile_repository.get_by_auth_user_id(auth_user_id)

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        return profile

    async def _settings(self, profile_id: UUID) -> UserSettings | None:
        return (
            await self.db.execute(select(UserSettings).where(UserSettings.profile_id == profile_id))
        ).scalar_one_or_none()

    async def _prefs(self, profile_id: UUID) -> SchedulePreference | None:
        return (
            await self.db.execute(
                select(SchedulePreference).where(SchedulePreference.profile_id == profile_id)
            )
        ).scalar_one_or_none()

    async def _pins(self, profile_id: UUID) -> dict[UUID, date]:
        rows = await self.db.execute(
            select(ScheduleOverride.unit_id, ScheduleOverride.date).where(
                ScheduleOverride.profile_id == profile_id
            )
        )

        return {unit_id: when for unit_id, when in rows.all()}

    async def _units(self, profile: Profile) -> tuple[object | None, list[PlanUnit]]:
        """The active roadmap and its lessons in order. A paused roadmap has no
        plan, so it is not on the calendar until it is resumed."""
        roadmap = await self.roadmap_repository.get_active_for_profile(profile.id)

        if roadmap is None:
            return None, []

        rows = await get_roadmap_learning_units(
            db=self.db, user_id=profile.auth_user_id, roadmap_id=roadmap.id
        )

        units = [
            PlanUnit(
                id=unit.id,
                task_id=task.id,
                task_title=task.title,
                title=unit.title,
                type=unit.type.value if hasattr(unit.type, "value") else str(unit.type),
                minutes=unit.estimated_minutes,
                completed=unit.completed,
            )
            for _, _, task, unit in rows
        ]

        return roadmap, units

    async def _plan(self, profile: Profile, settings):
        today = local_today(getattr(settings, "timezone", None) or profile.timezone)
        roadmap, units = await self._units(profile)
        prefs = await self._prefs(profile.id)
        pins = await self._pins(profile.id)
        availability = availability_for(profile, settings, prefs)

        # Pins on lessons that are gone or finished are ignored by the planner.
        result = plan(units, today, availability, pins)

        return roadmap, units, prefs, pins, availability, result, today

    # ---- reading the plan -------------------------------------------------------------------------------------------

    async def schedule(self, auth_user_id: UUID) -> dict:
        profile = await self._profile(auth_user_id)
        settings = await self._settings(profile.id)
        roadmap, _, prefs, _, availability, result, today = await self._plan(profile, settings)

        return {
            "roadmap_id": roadmap.id if roadmap else None,
            "roadmap_title": roadmap.title if roadmap else None,
            "today": today,
            "days": serialise(result, today),
            "unscheduled": len(result.unscheduled),
            "availability": {
                "weekday_minutes": availability.weekday_minutes,
                "blocked_dates": sorted(d.isoformat() for d in availability.blocked),
                "start": availability.start,
            },
            "preferences": {
                "note": prefs.note if prefs else None,
                "active": bool(prefs and (prefs.weekday_minutes or prefs.blocked_dates or prefs.start_time)),
            },
        }

    # ---- moving lessons ---------------------------------------------------------------------------------------------------

    async def _movable_unit(self, profile: Profile, unit_id: UUID) -> PlanUnit:
        _, units = await self._units(profile)
        unit = next((u for u in units if u.id == unit_id), None)

        if unit is None:
            raise HTTPException(status_code=404, detail="Lesson not found in your current plan")

        if unit.completed:
            raise HTTPException(status_code=409, detail="That lesson is already finished.")

        return unit

    async def move(self, auth_user_id: UUID, unit_id: UUID, when: date) -> dict:
        profile = await self._profile(auth_user_id)
        settings = await self._settings(profile.id)
        today = local_today(getattr(settings, "timezone", None) or profile.timezone)

        if when < today:
            raise HTTPException(status_code=422, detail="Pick today or a later day.")

        if when > today + timedelta(days=MOVE_HORIZON_DAYS):
            raise HTTPException(status_code=422, detail="That is too far ahead.")

        await self._movable_unit(profile, unit_id)

        await self.db.execute(
            insert(ScheduleOverride)
            .values(profile_id=profile.id, unit_id=unit_id, date=when)
            .on_conflict_do_update(
                index_elements=["profile_id", "unit_id"], set_={"date": when}
            )
        )
        await self.db.commit()

        return await self.schedule(auth_user_id)

    async def unpin(self, auth_user_id: UUID, unit_id: UUID) -> dict:
        profile = await self._profile(auth_user_id)

        await self.db.execute(
            delete(ScheduleOverride).where(
                ScheduleOverride.profile_id == profile.id,
                ScheduleOverride.unit_id == unit_id,
            )
        )
        await self.db.commit()

        return await self.schedule(auth_user_id)

    # ---- telling the planner about your time (AI) ----------------------------------------------------------------------------

    async def optimise(self, auth_user_id: UUID, request: str) -> dict:
        profile = await self._profile(auth_user_id)
        settings = await self._settings(profile.id)
        today = local_today(getattr(settings, "timezone", None) or profile.timezone)

        since = datetime.now(timezone.utc) - timedelta(hours=24)
        used = (
            await self.db.execute(
                select(func.count()).select_from(AiRequest).where(
                    AiRequest.profile_id == profile.id,
                    AiRequest.purpose == "planner",
                    AiRequest.success.is_(True),
                    AiRequest.created_at >= since,
                )
            )
        ).scalar_one()

        if used >= OPTIMISE_DAILY_LIMIT:
            raise HTTPException(
                status_code=429,
                detail=f"You have used today's {OPTIMISE_DAILY_LIMIT} schedule changes. Try again tomorrow.",
            )

        usual = clamp_daily_minutes((profile.daily_hours or 2) * 60)
        skipped = "Saturday, Sunday" if profile.weekend_study is False else "none"

        prompt = PLANNER_PROMPT.format(
            today=today.isoformat(),
            weekday=WEEKDAY_NAMES[today.weekday()],
            usual=usual,
            skipped=skipped,
            request=request.strip(),
        )

        use_profile(profile.id, profile.language)
        rules = None

        for _ in range(2):
            try:
                text = await self._ask(
                    [
                        {"role": "system", "content": "You turn schedules into planner rules. You output only JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    purpose="planner",
                    temperature=0.1,
                    max_tokens=700,
                    json_mode=True,
                    profile_id=profile.id,
                    prompt_version=prompt_version("planner"),
                )
                rules = PlannerRules(**parse_ai_json(text))
                break
            except AIUnavailableError:
                break
            except (ValueError, ValidationError):
                logger.warning("Planner answer rejected")

        if rules is None:
            raise HTTPException(
                status_code=502,
                detail="We could not understand that right now. Please try again.",
            )

        weekday, blocked = rules.rules_for(today)
        prefs = await self._prefs(profile.id)

        if prefs is None:
            prefs = SchedulePreference(profile_id=profile.id)
            self.db.add(prefs)

        prefs.weekday_minutes = weekday
        prefs.blocked_dates = blocked
        prefs.start_time = None
        prefs.note = request.strip()[:500]

        if rules.start:
            prefs.start_time = PART_OF_DAY_START[rules.start]

        await self.notifications.create_once(
            profile_id=profile.id,
            type=TYPE_SCHEDULE,
            title=message("plan_updated", profile.language),
            body=rules.summary,
            url="/calendar",
            dedupe_key=f"optimise:{datetime.now(timezone.utc).isoformat()}",
        )
        await self.db.commit()

        result = await self.schedule(auth_user_id)
        result["summary"] = rules.summary

        return result

    async def reset_preferences(self, auth_user_id: UUID) -> dict:
        profile = await self._profile(auth_user_id)

        await self.db.execute(
            delete(SchedulePreference).where(SchedulePreference.profile_id == profile.id)
        )
        await self.db.commit()

        return await self.schedule(auth_user_id)

    # ---- missed lessons -----------------------------------------------------------------------------------------------------------

    async def roll_over(self, profile: Profile, settings) -> int:
        """Once per learner day: compare today's plan with yesterday's, and if
        lessons were missed (and not pinned) tell the learner they moved.
        Returns how many moved. The caller commits."""
        snapshot = (
            await self.db.execute(
                select(ScheduleSnapshot).where(ScheduleSnapshot.profile_id == profile.id)
            )
        ).scalar_one_or_none()

        # Already done today (this runs every few minutes): nothing to compute.
        if snapshot is not None and snapshot.day >= local_today(
            getattr(settings, "timezone", None) or profile.timezone
        ):
            return 0

        roadmap, units, _, pins, _, result, today = await self._plan(profile, settings)

        planned_today = {
            str(p.unit.id): day.date.isoformat() for day in result.days for p in day.placed
        }
        moved = 0

        if snapshot is not None:
            open_ids = {str(u.id) for u in units if not u.completed}

            for unit_id, planned in (snapshot.plan or {}).items():
                if (
                    unit_id in open_ids
                    and date.fromisoformat(planned) < today
                    and UUID(unit_id) not in pins
                ):
                    moved += 1

        if snapshot is None:
            self.db.add(ScheduleSnapshot(profile_id=profile.id, day=today, plan=planned_today))
        else:
            snapshot.day = today
            snapshot.plan = planned_today

        if moved:
            last = max((d.date for d in result.days), default=None)

            await self.notifications.create_once(
                profile_id=profile.id,
                type=TYPE_SCHEDULE,
                title=message("moved_one" if moved == 1 else "moved_other", profile.language, count=moved),
                body=(
                    message("moved_until", profile.language, date=short_date(last, profile.language))
                    if last
                    else message("moved_missed", profile.language)
                ),
                url="/calendar",
                dedupe_key=f"rollover:{today.isoformat()}",
            )

        await self.db.flush()

        return moved

    # ---- subscription feed ----------------------------------------------------------------------------------------------------------

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
        profile = (
            await self.db.execute(select(Profile).where(Profile.calendar_token == token))
        ).scalar_one_or_none()

        # Same answer for a wrong or revoked token.
        if profile is None:
            raise HTTPException(status_code=404, detail="Calendar not found")

        settings = await self._settings(profile.id)
        roadmap, _, _, _, _, result, today = await self._plan(profile, settings)

        # Past missed lessons are not worth a calendar event.
        days = [d for d in serialise(result, today) if d["date"] >= today]

        return build_ics(days, roadmap.id if roadmap else None)
