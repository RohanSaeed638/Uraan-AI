import asyncio
import json
import logging

from openai import AsyncOpenAI
from pydantic import ValidationError

from app.ai.parser import parse_ai_json
from app.ai.prompts.learning_units_prompt import (
    EXPAND_NOTE,
    OUTLINE_PROMPT,
    PROJECT_PROMPT,
    READING_PROMPT,
    STYLE_LABELS,
    rules_for,
)
from app.ai.schemas.learning_plan_schema import (
    ALLOWED_TYPES,
    LearningPlan,
    PROJECT_FLOOR_WORDS,
    PROJECT_TARGET_WORDS,
    PlanUnit,
    READING_FLOOR_WORDS,
    READING_TARGET_WORDS,
    normalize_order,
    style_key,
    validate_plan,
    word_count,
)
from app.ai.services.video_resolver import resolve_many
from app.core.config import settings

logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY
)

OUTLINE_ATTEMPTS = 2
OUTLINE_TOKENS = 3000
BODY_TOKENS = 2200
PARALLEL_WRITERS = 4

SYSTEM_JSON = "You are an expert teacher and course planner. You output only JSON."
SYSTEM_TEXT = (
    "You are an expert teacher who writes accurate, clear, complete lessons "
    "in Markdown."
)


def _enum_value(value) -> str:
    return str(getattr(value, "value", value) or "")


def build_outline_prompt(roadmap, task) -> str:
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
        allowed_types=", ".join(sorted(ALLOWED_TYPES[style])),
        type_rules=rules_for(style),
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
        kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_completion_tokens=max_tokens,
            **kwargs,
        )

        content = response.choices[0].message.content

        if not content or not content.strip():
            raise ValueError("AI returned an empty response.")

        return content

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

    async def generate(self, roadmap, task) -> list[dict]:
        """Validated lessons as dicts ready for `TaskLearningUnit(**d)`."""
        prompt = build_outline_prompt(roadmap, task)
        last_error: Exception | None = None

        for attempt in range(1, OUTLINE_ATTEMPTS + 1):
            try:
                plan = await self._outline(prompt)
                validate_plan(plan, roadmap.learning_style)
                break
            except (ValueError, ValidationError, json.JSONDecodeError) as exc:
                last_error = exc
                logger.warning("Outline attempt %s rejected: %s", attempt, exc)
        else:
            raise ValueError(f"No usable lesson plan: {last_error}")

        units = normalize_order(plan)

        gate = asyncio.Semaphore(PARALLEL_WRITERS)

        async def body(unit: PlanUnit) -> str | None:
            if unit.type == "video":
                return (unit.notes or "").strip() or None

            async with gate:
                return await self._write(unit, units, roadmap, task)

        videos = [u for u in units if u.type == "video"]

        bodies, urls = await asyncio.gather(
            asyncio.gather(*(body(u) for u in units)),
            resolve_many(
                [
                    (u.video_urls, u.search_query, f"{task.title} {u.title}")
                    for u in videos
                ]
            ),
        )

        resolved = {id(u): url for u, url in zip(videos, urls)}

        return [
            {
                "day": u.day,
                "order": u.order,
                "type": u.type,
                "title": u.title[:255],
                "description": u.description or None,
                "content": content,
                "resource_url": resolved.get(id(u)),
                "estimated_minutes": u.estimated_minutes,
            }
            for u, content in zip(units, bodies)
        ]
