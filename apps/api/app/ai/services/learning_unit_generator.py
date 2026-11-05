import asyncio
import json
import logging

from pydantic import ValidationError

from app.ai.llm import complete_text
from app.ai.parser import parse_ai_json
from app.ai.versions import prompt_version
from app.ai.prompts.learner_context import learner_context
from app.ai.prompts.learning_units_prompt import (
    EXERCISE_PROMPT,
    EXPAND_NOTE,
    OUTLINE_PROMPT,
    PROJECT_PROMPT,
    READING_PROMPT,
    STYLE_LABELS,
    rules_for,
)
from app.ai.schemas.exercise_schema import ExerciseOutput
from app.ai.schemas.learning_plan_schema import (
    LearningPlan,
    PROJECT_LEVELS,
    PROJECT_FLOOR_WORDS,
    PROJECT_TARGET_WORDS,
    PlanUnit,
    READING_FLOOR_WORDS,
    READING_TARGET_WORDS,
    allowed_types,
    normalize_order,
    style_key,
    trim_exercises,
    validate_plan,
    word_count,
)
from app.ai.services.video_resolver import resolve_many
from app.core.career_catalog import is_coding_career

logger = logging.getLogger(__name__)

OUTLINE_ATTEMPTS = 2
OUTLINE_TOKENS = 4500
BODY_TOKENS = 2200
PARALLEL_WRITERS = 4

SYSTEM_JSON = "You are an expert teacher and course planner. You output only JSON."
SYSTEM_TEXT = (
    "You are an expert teacher who writes accurate, clear, complete lessons "
    "in Markdown."
)


def _enum_value(value) -> str:
    return str(getattr(value, "value", value) or "")


def build_outline_prompt(roadmap, task, profile=None, coding: bool = False) -> str:
    style = style_key(roadmap.learning_style)

    return OUTLINE_PROMPT.format(
        career=roadmap.career_slug or "not specified",
        skill=_enum_value(roadmap.skill_level) or "not specified",
        learning_goal=roadmap.learning_goal or "not specified",
        daily_hours=roadmap.daily_hours or 2,
        style_label=STYLE_LABELS[style],
        task_title=task.title,
        task_description=task.description or "not provided",
        task_hours=task.estimated_hours or 2,
        resource_links=", ".join(task.resource_links or []) or "none",
        allowed_types=", ".join(sorted(allowed_types(style, coding))),
        type_rules=rules_for(style, coding),
        learner_context=learner_context(profile),
    )


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) or "- (none)"


def build_body_prompt(unit: PlanUnit, units: list[PlanUnit], roadmap, task) -> str:
    template, target = (
        (PROJECT_PROMPT, PROJECT_TARGET_WORDS)
        if unit.type == "project"
        else (READING_PROMPT, READING_TARGET_WORDS)
    )

    return template.format(
        task_title=task.title,
        title=unit.title,
        description=unit.description or unit.title,
        skill=_enum_value(roadmap.skill_level) or "not specified",
        career=roadmap.career_slug or "not specified",
        minutes=unit.estimated_minutes,
        outline=_bullets(unit.outline),
        siblings=_bullets(
            [f"Day {u.day}: {u.title}" for u in units if u is not unit]
        ),
        target=target,
    )


def project_details(unit: PlanUnit) -> dict:
    """The project difficulty, skills and portfolio value, tidied."""
    level = (unit.difficulty or "").strip().lower()
    skills: list[str] = []

    for skill in unit.skills:
        skill = skill.strip()

        if skill and skill not in skills:
            skills.append(skill)

    return {
        "difficulty": level if level in PROJECT_LEVELS else None,
        "skills": skills[:5],
        "portfolio_value": (unit.portfolio_value or "").strip() or None,
    }


def strip_fence(text: str) -> str:
    """Removes a ```markdown fence wrapped around the whole answer."""
    text = text.strip()

    if text.startswith("```") and text.endswith("```") and "\n" in text:
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]

    return text.strip()


class LearningUnitGenerator:
    """Writes the day-by-day lessons for one task: an outline first, then
    each reading and project written in its own call, in parallel."""

    async def _chat(
        self,
        prompt: str,
        system: str,
        max_tokens: int,
        json_mode: bool,
    ) -> str:
        return await complete_text(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            purpose="lessons",
            temperature=0.4,
            max_tokens=max_tokens,
            json_mode=json_mode,
            prompt_version=prompt_version("lessons"),
        )

    async def _outline(self, prompt: str) -> LearningPlan:
        content = await self._chat(
            prompt, SYSTEM_JSON, OUTLINE_TOKENS, json_mode=True
        )

        return LearningPlan(**parse_ai_json(content))

    async def _write(self, unit: PlanUnit, units, roadmap, task) -> str:
        """The lesson body. Asks once more for a fuller version when the
        first draft is short, and rejects it if still too thin."""
        is_project = unit.type == "project"
        target = PROJECT_TARGET_WORDS if is_project else READING_TARGET_WORDS
        floor = PROJECT_FLOOR_WORDS if is_project else READING_FLOOR_WORDS

        prompt = build_body_prompt(unit, units, roadmap, task)

        text = strip_fence(
            await self._chat(prompt, SYSTEM_TEXT, BODY_TOKENS, json_mode=False)
        )

        if word_count(text) < target:
            retry = strip_fence(
                await self._chat(
                    prompt
                    + EXPAND_NOTE.format(words=word_count(text), target=target),
                    SYSTEM_TEXT,
                    BODY_TOKENS,
                    json_mode=False,
                )
            )
            text = max(text, retry, key=word_count)

        if word_count(text) < floor:
            raise ValueError(f"Lesson '{unit.title}' is too thin to teach from")

        return text

    async def _write_exercise(self, unit: PlanUnit, roadmap, task) -> ExerciseOutput:
        """A coding exercise as structured data. A draft that fails its checks
        (empty parts, Python that does not parse) is asked for once more."""
        prompt = EXERCISE_PROMPT.format(
            task_title=task.title,
            title=unit.title,
            description=unit.description or unit.title,
            language=unit.language,
            skill=_enum_value(roadmap.skill_level) or "not specified",
            career=roadmap.career_slug or "not specified",
            minutes=unit.estimated_minutes,
            outline=_bullets(unit.outline),
        )
        last: Exception | None = None

        for _ in range(2):
            try:
                content = await self._chat(
                    prompt, SYSTEM_JSON, BODY_TOKENS, json_mode=True
                )
                exercise = ExerciseOutput(**parse_ai_json(content))
                exercise.check()

                return exercise
            except (ValueError, ValidationError, json.JSONDecodeError) as exc:
                last = exc
                logger.warning("Exercise '%s' rejected: %s", unit.title, exc)

        raise ValueError(f"Exercise '{unit.title}' could not be written: {last}")

    async def outline_units(self, roadmap, task, profile=None) -> list[PlanUnit]:
        """The validated day-by-day plan: titles, types and what each lesson covers."""
        coding = getattr(roadmap, "coding_career", None)

        if coding is None:
            coding = is_coding_career(roadmap.career_slug)

        prompt = build_outline_prompt(roadmap, task, profile, coding)
        last_error: Exception | None = None

        for attempt in range(1, OUTLINE_ATTEMPTS + 1):
            try:
                plan = await self._outline(prompt)
                trim_exercises(plan)
                validate_plan(plan, roadmap.learning_style, coding)

                return normalize_order(plan)
            except (ValueError, ValidationError, json.JSONDecodeError) as exc:
                last_error = exc
                logger.warning("Outline attempt %s rejected: %s", attempt, exc)

        raise ValueError(f"No usable lesson plan: {last_error}")

    async def write_unit(self, unit: PlanUnit, units: list[PlanUnit], roadmap, task):
        """(lesson text, type-specific details) for one lesson."""
        if unit.type == "video":
            return (unit.notes or "").strip() or None, None

        if unit.type == "exercise":
            exercise = await self._write_exercise(unit, roadmap, task)

            return exercise.problem, exercise.as_details()

        text = await self._write(unit, units, roadmap, task)

        return text, project_details(unit) if unit.type == "project" else None

    @staticmethod
    def _row(unit: PlanUnit, content, details, url, status: str) -> dict:
        return {
            "day": unit.day,
            "order": unit.order,
            "type": unit.type,
            "title": unit.title[:255],
            "description": unit.description or None,
            "content": content,
            "details": details,
            "prompt_version": prompt_version("lessons"),
            "resource_url": url,
            "estimated_minutes": unit.estimated_minutes,
            "status": status,
        }

    async def generate_outline(self, roadmap, task, profile=None) -> list[dict]:
        """The plan, fast: every lesson is saved with its title, day and length,
        videos are finished (a link and notes), and each reading, project and
        exercise is marked `pending` with its outline kept in `details["_plan"]`
        for `write_unit` to fill in afterwards."""
        units = await self.outline_units(roadmap, task, profile)
        videos = [u for u in units if u.type == "video"]
        urls = await resolve_many(
            [(u.video_urls, u.search_query, f"{task.title} {u.title}") for u in videos]
        )
        resolved = {id(u): url for u, url in zip(videos, urls)}
        rows = []

        for u in units:
            if u.type == "video":
                rows.append(self._row(u, (u.notes or "").strip() or None, None, resolved.get(id(u)), "ready"))
            else:
                rows.append(self._row(u, None, {"_plan": u.model_dump()}, None, "pending"))

        return rows

    async def generate(self, roadmap, task, profile=None) -> list[dict]:
        """Validated lessons as dicts ready for `TaskLearningUnit(**d)`, every
        body written before it returns (see `generate_outline` for the quick path)."""
        units = await self.outline_units(roadmap, task, profile)
        gate = asyncio.Semaphore(PARALLEL_WRITERS)

        async def body(unit: PlanUnit):
            if unit.type == "video":
                return await self.write_unit(unit, units, roadmap, task)

            async with gate:
                return await self.write_unit(unit, units, roadmap, task)

        videos = [u for u in units if u.type == "video"]

        bodies, urls = await asyncio.gather(
            asyncio.gather(*(body(u) for u in units)),
            resolve_many(
                [(u.video_urls, u.search_query, f"{task.title} {u.title}") for u in videos]
            ),
        )

        resolved = {id(u): url for u, url in zip(videos, urls)}

        return [
            self._row(u, content, details, resolved.get(id(u)), "ready")
            for u, (content, details) in zip(units, bodies)
        ]
