
from app.ai.llm import complete_text
from app.ai.versions import prompt_version


PROMPT = """
Write a short portfolio description for one project, in the first person.

Project title: {title}
Technologies: {tech}
Related learning task: {task_title}
Project brief or instructions the learner followed:
{brief}

Rules:
1. 2 to 3 sentences, at most 450 characters.
2. Say what the project does and which technologies it uses.
3. Use ONLY the facts above. Do not invent features, users, metrics,
   results or deployment details.
4. Plain, specific language. No buzzwords. No quotation marks.
Output only the description.
"""


def build_prompt(
    title: str,
    tech: list[str],
    task_title: str | None,
    brief: str | None,
) -> str:
    return PROMPT.format(
        title=title,
        tech=", ".join(tech) if tech else "not specified",
        task_title=task_title or "not specified",
        brief=(brief or "").strip()[:3000] or "(none)",
    )


class PortfolioGenerator:

    async def draft_description(
        self,
        title: str,
        tech: list[str],
        task_title: str | None,
        brief: str | None,
    ) -> str:
        content = await complete_text(
            [
                {
                    "role": "system",
                    "content": "You write honest, concise portfolio copy.",
                },
                {
                    "role": "user",
                    "content": build_prompt(title, tech, task_title, brief),
                },
            ],
            purpose="portfolio",
            temperature=0.4,
            max_tokens=300,
            prompt_version=prompt_version("portfolio"),
        )

        return content.strip().strip('"')[:600]
