from openai import AsyncOpenAI

from app.ai.parser import parse_ai_json
from app.ai.prompts.quiz_prompt import QUIZ_PROMPT
from app.ai.schemas.quiz_schema import QuizOutput
from app.core.config import settings

QUESTION_COUNT = 5

client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY
)


class QuizGenerator:

    async def generate(
        self,
        profile,
        task,
    ) -> QuizOutput:

        lesson_titles = "\n".join(
            f"- {unit.title}"
            for unit in sorted(
                task.learning_units or [],
                key=lambda u: (u.day, u.order),
            )
        ) or "- (no lessons generated yet)"

        skill = getattr(profile.skill_level, "value", profile.skill_level)

        prompt = QUIZ_PROMPT.format(
            career=profile.career_slug or "",
            skill=skill or "",
            task_title=task.title,
            task_description=task.description or "",
            lesson_titles=lesson_titles,
            question_count=QUESTION_COUNT,
        )

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert software engineering "
                        "instructor who writes fair, clear quizzes."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.4,
        )

        raw_content = response.choices[0].message.content

        if not raw_content:
            raise ValueError("AI returned an empty quiz.")

        return QuizOutput(**parse_ai_json(raw_content))
