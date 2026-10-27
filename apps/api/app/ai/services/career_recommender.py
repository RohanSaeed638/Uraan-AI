import logging

from app.ai.llm import complete_text
from app.ai.parser import parse_ai_json
from app.ai.prompts.career_recommend_prompt import CAREER_RECOMMEND_PROMPT
from app.ai.versions import prompt_version

logger = logging.getLogger(__name__)

COUNT = 3


def catalogue_lines(careers) -> str:
    return "\n".join(
        f"{c.slug} | {c.name} | {c.difficulty} | {c.market_demand} | "
        f"{c.estimated_months} | {c.description[:110]}"
        for c in careers
    )


def pick_valid(raw, allowed: set[str]) -> list[dict]:
    """Keeps only catalogue slugs (each once) with a usable reason."""
    picked: list[dict] = []
    seen: set[str] = set()

    items = raw.get("recommendations") if isinstance(raw, dict) else None

    for item in items or []:
        if not isinstance(item, dict):
            continue

        slug = str(item.get("slug", "")).strip()
        reason = str(item.get("reason", "")).strip()

        if slug in allowed and slug not in seen and reason:
            seen.add(slug)
            picked.append({"slug": slug, "reason": reason})

    return picked[:COUNT]


class CareerRecommender:
    async def recommend(self, careers, answers: dict) -> list[dict]:
        prompt = CAREER_RECOMMEND_PROMPT.format(
            count=COUNT,
            interests=answers["interests"],
            experience=answers.get("experience") or "not given",
            education=answers.get("education") or "not given",
            daily_hours=answers.get("daily_hours") or "not given",
            goal=answers.get("goal") or "not given",
            catalogue=catalogue_lines(careers),
        )

        text = await complete_text(
            [
                {"role": "system", "content": "You recommend careers."},
                {"role": "user", "content": prompt},
            ],
            purpose="career",
            temperature=0.3,
            max_tokens=1200,
            json_mode=True,
            prompt_version=prompt_version("career"),
        )

        raw = parse_ai_json(text)

        return pick_valid(raw, {c.slug for c in careers})
