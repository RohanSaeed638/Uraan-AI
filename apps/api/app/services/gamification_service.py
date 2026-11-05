from datetime import date, datetime, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.achievement_catalog import career_title
from app.models.profile import Profile
from app.core.analytics import track
from app.models.xp_event import XPEvent

XP_LESSON_COMPLETED = 10
XP_TASK_COMPLETED = 25
XP_QUIZ_PASSED = 30
XP_INTERVIEW_COMPLETED = 40

XP_PER_LEVEL = 100

REASON_LESSON = "lesson_completed"
REASON_TASK = "task_completed"
REASON_QUIZ = "quiz_passed"
REASON_INTERVIEW = "interview_completed"


def level_for(xp: int) -> int:
    return 1 + max(xp, 0) // XP_PER_LEVEL


def local_today(tz_name: str | None, now: datetime | None = None) -> date:
    """The current date for the user, falling back to UTC."""
    now = now or datetime.now(timezone.utc)

    try:
        tz = ZoneInfo(tz_name) if tz_name else timezone.utc
    except ZoneInfoNotFoundError:
        tz = timezone.utc

    return now.astimezone(tz).date()


def next_streak(
    current: int,
    last_activity: date | None,
    today: date,
) -> int:
    """Streak after activity on `today`: same day keeps it, the next day
    extends it, any longer gap restarts at 1."""
    if last_activity == today:
        return max(current, 1)

    if last_activity == today - timedelta(days=1):
        return current + 1

    return 1


class GamificationService:
    """Awards XP and keeps the streak. Callers own the commit."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def award(
        self,
        profile: Profile,
        amount: int,
        reason: str,
        ref_id: UUID,
        evaluate: bool = True,
    ) -> bool:
        """Awards XP once per (profile, reason, ref). Returns whether this
        call was the one that awarded it. Unless `evaluate` is False the
        learner's achievements are checked afterwards (their own bonus XP
        passes False: the evaluation that paid it is already looping)."""
        stmt = (
            insert(XPEvent)
            .values(
                profile_id=profile.id,
                amount=amount,
                reason=reason,
                ref_id=ref_id,
            )
            .on_conflict_do_nothing(constraint="uq_xp_event_once")
            .returning(XPEvent.id)
        )

        inserted = (await self.db.execute(stmt)).scalar_one_or_none()

        if inserted is None:
            return False

        profile.xp = (profile.xp or 0) + amount
        track(profile.id, "xp_earned", reason=reason, amount=amount)

        today = local_today(profile.timezone)
        profile.streak_days = next_streak(
            profile.streak_days or 0,
            profile.last_activity_date,
            today,
        )
        profile.last_activity_date = today

        await self.db.flush()

        if evaluate:
            # Local import: the achievement service uses this class too.
            from app.services.achievement_service import AchievementService

            await AchievementService(self.db).safe_evaluate(profile)

        return True

    async def weekly_xp(self, profile: Profile) -> int:
        today = local_today(profile.timezone)
        week_start = today - timedelta(days=today.weekday())
        start = datetime.combine(
            week_start,
            datetime.min.time(),
            tzinfo=timezone.utc,
        )

        result = await self.db.execute(
            select(func.coalesce(func.sum(XPEvent.amount), 0)).where(
                XPEvent.profile_id == profile.id,
                XPEvent.created_at >= start,
            )
        )

        return int(result.scalar_one())

    async def summary(self, profile: Profile) -> dict:
        xp = profile.xp or 0
        today = local_today(profile.timezone)

        # A streak that wasn't extended yesterday or today has lapsed.
        streak = profile.streak_days or 0
        if profile.last_activity_date is None or (
            profile.last_activity_date < today - timedelta(days=1)
        ):
            streak = 0

        title = career_title(xp)

        return {
            "xp": xp,
            "career_title": title["title"],
            "next_career_title": title["next_title"],
            "xp_to_next_title": title["xp_to_next"],
            "title_progress": round(title["progress"], 3),
            "level": level_for(xp),
            "xp_into_level": xp % XP_PER_LEVEL,
            "xp_per_level": XP_PER_LEVEL,
            "streak_days": streak,
            "active_today": profile.last_activity_date == today,
            "weekly_xp": await self.weekly_xp(profile),
        }
