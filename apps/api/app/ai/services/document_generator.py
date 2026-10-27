from app.ai.llm import complete_text
from app.ai.versions import prompt_version
from app.ai.prompts.document_prompt import (
    DOCUMENT_PROMPT,
    KIND_INSTRUCTIONS,
    KIND_LABELS,
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

        content = await complete_text(
            [
                {
                    "role": "system",
                    "content": (
                        "You write honest, well-structured career "
                        "documents and never invent facts."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            purpose="document",
            temperature=0.4,
            max_tokens=1500,
            prompt_version=prompt_version("document"),
        )

        return content.strip()
