"""The daily motivational message: written once a day from the learner's real
progress, saved, and reused for the dashboard and the reminder."""
import logging

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm import complete_text
from app.ai.prompts.language import LANGUAGES
from app.core.texts import text
from app.ai.prompts.mentor_prompt import TONES
from app.ai.prompts.motivation_prompt import MOTIVATION_PROMPT
from app.ai.versions import prompt_version
from app.models.daily_motivation import DailyMotivation
from app.repositories.learning_repository import get_next_learning_unit
from app.repositories.profile_repository import ProfileRepository
from app.repositories.roadmap_task_repository import RoadmapTaskRepository
from app.repositories.settings_repository import SettingsRepository
from app.services.gamification_service import GamificationService, local_today

logger = logging.getLogger(__name__)

MAX_CHARS = 280


def fallback_message(facts: dict, language: str | None = None) -> str:
    """Used when the AI cannot answer, so the dashboard never has a gap."""
    streak = facts.get("streak_days", 0)
    lesson = facts.get("next_lesson")

    if streak >= 2:
        base = text("fallback_streak", language, days=streak)
    elif facts.get("active_today"):
        base = text("fallback_today", language)
    else:
        base = text("fallback_start", language)

    return (
        text("fallback_next", language, base=base, lesson=lesson)
        if lesson
        else text("fallback_pick", language, base=base)
    )


def facts_text(facts: dict) -> str:
    lines = [
        f"- Name: {facts['name']}",
        f"- Current streak: {facts['streak_days']} day(s)",
        f"- XP earned this week: {facts['weekly_xp']}",
        f"- Studied today already: {'yes' if facts['active_today'] else 'not yet'}",
    ]

    if facts.get("tasks_total"):
        lines.append(f"- Roadmap progress: {facts['tasks_done']} of {facts['tasks_total']} tasks done")
    if facts.get("next_lesson"):
        lines.append(f"- Next lesson: \"{facts['next_lesson']}\"")

    return "\n".join(lines)


def clean(message: str | None) -> str | None:
    """The model's answer as a single plain line, or None if unusable."""
    text = " ".join((message or "").split()).strip("\"' ")

    if len(text) < 10 or len(text) > MAX_CHARS:
        return None

    return text


class MotivationService:
    def __init__(self, db: AsyncSession, ask=None):
        self.db = db
        self.profiles = ProfileRepository(db)
        self.settings = SettingsRepository(db)
        self._ask = ask or complete_text

    async def _facts(self, profile) -> dict:
        summary = await GamificationService(self.db).summary(profile)
        next_unit = await get_next_learning_unit(self.db, profile.auth_user_id)
        facts = {
            "name": (profile.full_name or "").split(" ")[0] or "the learner",
            "streak_days": summary["streak_days"],
            "weekly_xp": summary["weekly_xp"],
            "active_today": summary["active_today"],
        }

        if next_unit is not None:
            progress = await RoadmapTaskRepository(self.db).get_roadmap_progress(next_unit[0].id)
            facts.update(
                next_lesson=next_unit[3].title,
                tasks_done=progress["completed"],
                tasks_total=progress["total"],
            )

        return facts

    async def for_profile(self, profile, settings_row=None) -> dict:
        """Today's message for this learner: {message, day, source}."""
        if settings_row is None:
            settings_row = await self.settings.get_by_profile_id(profile.id)

        day = local_today(getattr(settings_row, "timezone", None) or profile.timezone)

        saved = (
            await self.db.execute(
                select(DailyMotivation).where(
                    DailyMotivation.profile_id == profile.id,
                    DailyMotivation.day == day,
                )
            )
        ).scalar_one_or_none()

        if saved is not None:
            return {"message": saved.message, "day": day, "source": saved.source}

        facts = await self._facts(profile)

        # With the AI mentor switched off, no AI is used anywhere.
        if settings_row is not None and not settings_row.ai_mentor_enabled:
            return {"message": fallback_message(facts, profile.language), "day": day, "source": "fallback"}

        tone = getattr(settings_row, "ai_tone", None) or "friendly"
        prompt = MOTIVATION_PROMPT.format(
            tone=TONES.get(tone, TONES["friendly"]),
            language=LANGUAGES.get(profile.language or "en", LANGUAGES["en"]),
            facts=facts_text(facts),
        )

        try:
            message = clean(
                await self._ask(
                    [
                        {"role": "system", "content": "You write short, kind motivational messages."},
                        {"role": "user", "content": prompt},
                    ],
                    purpose="motivation",
                    temperature=0.8,
                    max_tokens=150,
                    profile_id=profile.id,
                    prompt_version=prompt_version("motivation"),
                )
            )
        except Exception:
            logger.exception("Daily motivation failed")
            message = None

        # Not saved when it fell back, so the AI is tried again next time.
        if message is None:
            return {"message": fallback_message(facts, profile.language), "day": day, "source": "fallback"}

        # A second request on the same day loses the race harmlessly.
        await self.db.execute(
            insert(DailyMotivation)
            .values(
                profile_id=profile.id,
                day=day,
                message=message,
                source="ai",
                prompt_version=prompt_version("motivation"),
            )
            .on_conflict_do_nothing(index_elements=["profile_id", "day"])
        )
        await self.db.commit()

        winner = (
            await self.db.execute(
                select(DailyMotivation.message).where(
                    DailyMotivation.profile_id == profile.id,
                    DailyMotivation.day == day,
                )
            )
        ).scalar_one()

        return {"message": winner, "day": day, "source": "ai"}

    async def today(self, auth_user_id) -> dict:
        profile = await self.profiles.get_by_auth_user_id(auth_user_id)

        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        return await self.for_profile(profile)
