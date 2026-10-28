from app.ai.llm import complete_text
from app.ai.parser import parse_ai_json
from app.ai.versions import prompt_version
from app.ai.prompts.interview_prompt import (
    ANSWER_PROMPT,
    QUESTIONS_PROMPT,
    SUMMARY_PROMPT,
)
from app.ai.schemas.interview_schema import (
    AnswerFeedbackOutput,
    QUESTION_COUNT,
    QuestionsOutput,
    SummaryOutput,
)
SYSTEM = "You are a fair, specific interview coach. You output only JSON."


async def _ask(prompt: str, max_tokens: int) -> dict:
    content = await complete_text(
        [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        purpose="interview",
        temperature=0.4,
        max_tokens=max_tokens,
        json_mode=True,
        prompt_version=prompt_version("interview"),
    )

    return parse_ai_json(content)


def format_results(turns: list) -> str:
    lines = []

    for turn in turns:
        lines.append(
            f"Q{turn.order}: technical {turn.technical_score}, "
            f"communication {turn.communication_score}, "
            f"confidence {turn.confidence_score}. "
            f"Question: {turn.question}"
        )

    return "\n".join(lines)


class InterviewGenerator:

    async def questions(
        self,
        role: str,
        difficulty: str,
        career: str | None,
    ) -> list[str]:
        data = await _ask(
            QUESTIONS_PROMPT.format(
                count=QUESTION_COUNT,
                difficulty=difficulty,
                role=role,
                career=career or "not specified",
            ),
            max_tokens=800,
        )

        return QuestionsOutput(**data).questions

    async def grade(
        self,
        role: str,
        difficulty: str,
        question: str,
        answer: str,
    ) -> AnswerFeedbackOutput:
        data = await _ask(
            ANSWER_PROMPT.format(
                role=role,
                difficulty=difficulty,
                question=question,
                answer=answer,
            ),
            max_tokens=500,
        )

        return AnswerFeedbackOutput(**data)

    async def summarize(
        self,
        role: str,
        difficulty: str,
        answered_turns: list,
    ) -> SummaryOutput:
        data = await _ask(
            SUMMARY_PROMPT.format(
                role=role,
                difficulty=difficulty,
                results=format_results(answered_turns),
            ),
            max_tokens=500,
        )

        return SummaryOutput(**data)
