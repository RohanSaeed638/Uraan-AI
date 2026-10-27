from app.ai.llm import complete_text
from app.ai.prompts.mentor_prompt import build_system_prompt
from app.ai.versions import prompt_version


class MentorAIService:
    """Turns a chat history into the mentor's next reply."""

    async def generate_response(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        profile_id=None,
    ) -> str:
        reply = await complete_text(
            [
                {
                    "role": "system",
                    "content": system_prompt or build_system_prompt(None, None, ""),
                },
                *messages,
            ],
            purpose="mentor",
            temperature=0.5,
            max_tokens=1200,
            profile_id=profile_id,
            prompt_version=prompt_version("mentor"),
        )

        return reply.strip()
