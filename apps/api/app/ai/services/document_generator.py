from openai import AsyncOpenAI

from app.ai.prompts.document_prompt import (
    DOCUMENT_PROMPT,
    KIND_INSTRUCTIONS,
    KIND_LABELS,
)
from app.core.config import settings

client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY
)

NONE_YET = "(none yet)"


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else NONE_YET


def build_prompt(
    kind: str,
    profile,
    target_role: str,
    completed_tasks: list[str],
    projects: list[str],
    details: str | None,
    job_description: str | None,
) -> str:
    skill = getattr(profile.skill_level, "value", profile.skill_level)

    return DOCUMENT_PROMPT.format(
        kind_label=KIND_LABELS[kind],
        kind_instructions=KIND_INSTRUCTIONS[kind],
        name=profile.full_name or "[Your name]",
        target_role=target_role,
        skill=skill or "not specified",
        learning_goal=profile.learning_goal or "not specified",
        completed_tasks=_bullets(completed_tasks),
        projects=_bullets(projects),
        details=(details or "").strip() or NONE_YET,
        job_description=(job_description or "").strip() or NONE_YET,
    )


class DocumentGenerator:

    async def generate(
        self,
        kind: str,
        profile,
        target_role: str,
        completed_tasks: list[str],
        projects: list[str],
        details: str | None,
        job_description: str | None,
    ) -> str:
        prompt = build_prompt(
            kind,
            profile,
            target_role,
            completed_tasks,
            projects,
            details,
            job_description,
        )

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You write honest, well-structured career "
                        "documents and never invent facts."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_completion_tokens=1500,
        )

        content = response.choices[0].message.content

        if not content or not content.strip():
            raise ValueError("AI returned an empty document.")

        return content.strip()
