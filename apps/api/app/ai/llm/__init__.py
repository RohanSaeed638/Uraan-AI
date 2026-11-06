"""The one door to AI models.

    from app.ai.llm import complete_text

    text = await complete_text(messages, purpose="quiz", json_mode=True)

Generators never talk to a provider directly, so a provider outage is handled
in one place (see `router.py`) and every call is recorded in `ai_requests`.
"""
from functools import lru_cache

from app.ai.llm.context import current_language, current_profile, use_profile
from app.ai.prompts.language import generation_rule
from app.ai.llm.router import LLMRouter, build_providers
from app.ai.llm.types import AIBudgetExceeded, AIUnavailableError, LLMError, LLMRequest, LLMResult
from app.core.config import settings

__all__ = [
    "AIBudgetExceeded",
    "AIUnavailableError",
    "LLMError",
    "LLMRequest",
    "LLMResult",
    "complete",
    "complete_text",
    "get_router",
    "use_profile",
]


async def _record_to_db(row: dict) -> None:
    from app.db.session import SessionLocal
    from app.models.ai_request import AiRequest

    async with SessionLocal() as db:
        db.add(AiRequest(**row))
        await db.commit()


async def tokens_used_today(profile_id) -> int:
    """Input plus output tokens this learner's AI calls have used since midnight (UTC)."""
    from datetime import datetime, timezone

    from sqlalchemy import func, select

    from app.db.session import SessionLocal
    from app.models.ai_request import AiRequest

    midnight = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    async with SessionLocal() as db:
        return int(
            (
                await db.execute(
                    select(func.coalesce(func.sum(func.coalesce(AiRequest.input_tokens, 0) + func.coalesce(AiRequest.output_tokens, 0)), 0))
                    .where(AiRequest.profile_id == profile_id, AiRequest.created_at >= midnight)
                )
            ).scalar_one()
        )


async def check_budget(profile_id) -> None:
    """Refuses the call when the learner has spent their daily allowance. A failure to count is never
    a reason to refuse: the limit is a safety net, not a gate."""
    limit = settings.AI_DAILY_TOKENS_PER_USER

    if not limit or profile_id is None:
        return

    try:
        used = await tokens_used_today(profile_id)
    except Exception:
        return

    if used >= limit:
        raise AIBudgetExceeded("Daily AI allowance used up.")


@lru_cache
def get_router() -> LLMRouter:
    return LLMRouter(build_providers(settings), recorder=_record_to_db)


# Written for the learner to read in the app, so they follow their language.
# Not here: the mentor and motivation prompts set their own language; the
# planner reads text and returns rules; resumes, portfolios and interviews are
# for employers and stay in English.
LOCALISED_PURPOSES = {"roadmap", "roadmap_adapt", "lessons", "quiz", "career", "review"}


# For every request, whatever the feature or tone: the product reads as calm and professional.
STYLE_RULE = "Style rule: never use emoji or emoticons in any text you write."


async def complete(request: LLMRequest) -> LLMResult:
    if request.profile_id is None:
        request.profile_id = current_profile()

    await check_budget(request.profile_id)

    request.messages = [*request.messages, {"role": "system", "content": STYLE_RULE}]

    rule = generation_rule(current_language()) if request.purpose in LOCALISED_PURPOSES else ""

    if rule:
        request.messages = [*request.messages, {"role": "system", "content": "Language rules:\n" + rule}]

    return await get_router().complete(request)


async def complete_text(
    messages: list[dict],
    *,
    purpose: str,
    temperature: float = 0.4,
    max_tokens: int = 1500,
    json_mode: bool = False,
    profile_id=None,
    prompt_version: str | None = None,
) -> str:
    """Just the answer text: what most generators need."""
    result = await complete(
        LLMRequest(
            messages=messages,
            purpose=purpose,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
            profile_id=profile_id,
            prompt_version=prompt_version,
        )
    )

    return result.text
