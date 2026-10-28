from app.ai.llm import complete_text
from app.ai.versions import prompt_version

from app.ai.prompts.roadmap_prompt import ROADMAP_PROMPT
from app.ai.prompts.roadmap_adapt_prompt import ADAPT_REASONS, ROADMAP_ADAPT_PROMPT
from app.ai.prompts.learner_context import learner_context
from app.ai.prompts.career_template import career_template
from app.ai.parser import parse_ai_json
from app.ai.schemas.roadmap_schema import RoadmapOutput


def _value(item) -> str:
    """'beginner' for CareerStage.BEGINNER, so prompts never show 'CareerStage.X'."""
    return str(getattr(item, "value", item))


def _bullets(lines: list[str]) -> str:
    return "\n".join(f"- {line}" for line in lines) or "- (nothing)"


class RoadmapGenerator:

    async def _complete(
        self, prompt: str, system: str, purpose: str = "roadmap"
    ) -> RoadmapOutput:
        text = await complete_text(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            purpose=purpose,
            temperature=0.5,
            max_tokens=8000,
            json_mode=True,
            prompt_version=prompt_version(purpose),
        )

        return RoadmapOutput(**parse_ai_json(text))

    async def generate(
        self,
        profile,
        data,
        career=None,
    ) -> RoadmapOutput:
        """A whole new roadmap. `data` is what the learner asked for (the
        request, or a stored roadmap: both carry the same fields)."""
        prompt = ROADMAP_PROMPT.format(
            name=profile.full_name,
            career=data.career_slug,
            career_stage=_value(data.career_stage),
            skill=_value(data.skill_level),
            learning_goal=data.learning_goal,
            learning_style=_value(data.learning_style),
            daily_hours=data.daily_hours,
            duration=data.target_duration,
            learner_context=learner_context(profile),
            career_template=career_template(career),
        )

        return await self._complete(prompt, "You generate career roadmaps.")

    async def adapt(
        self,
        profile,
        roadmap,
        *,
        completed: list[str],
        unfinished: list[str],
        daily_hours: int,
        months_left: int,
        reason: str,
        note: str | None = None,
        career=None,
    ) -> RoadmapOutput:
        """Re-plans only the unfinished part of `roadmap`."""
        why = ADAPT_REASONS[reason]

        if note:
            why += f"\nThe learner adds: {note}"

        prompt = ROADMAP_ADAPT_PROMPT.format(
            name=profile.full_name,
            career=roadmap.career_slug,
            career_stage=_value(roadmap.career_stage),
            skill=_value(roadmap.skill_level),
            learning_goal=roadmap.learning_goal,
            learning_style=_value(roadmap.learning_style),
            daily_hours=daily_hours,
            months_left=months_left,
            weeks_left=months_left * 4,
            learner_context=learner_context(profile),
            career_template=career_template(career),
            reason=why,
            completed=_bullets(completed),
            unfinished=_bullets(unfinished),
        )

        return await self._complete(prompt, "You adapt career roadmaps.", "roadmap_adapt")
