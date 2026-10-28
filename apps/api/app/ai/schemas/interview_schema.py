from pydantic import BaseModel, Field, field_validator

QUESTION_COUNT = 5


class QuestionsOutput(BaseModel):
    questions: list[str] = Field(min_length=QUESTION_COUNT, max_length=QUESTION_COUNT)

    @field_validator("questions")
    @classmethod
    def non_empty_distinct(cls, value):
        cleaned = [q.strip() for q in value]

        if any(not q for q in cleaned):
            raise ValueError("Questions cannot be empty")

        if len({q.lower() for q in cleaned}) != len(cleaned):
            raise ValueError("Questions must be distinct")

        return cleaned


class AnswerFeedbackOutput(BaseModel):
    technical: int = Field(ge=0, le=10)
    communication: int = Field(ge=0, le=10)
    confidence: int = Field(ge=0, le=10)
    feedback: str = Field(min_length=1)


class SummaryOutput(BaseModel):
    strengths: list[str] = Field(default_factory=list, max_length=5)
    improvements: list[str] = Field(default_factory=list, max_length=5)
    next_steps: list[str] = Field(default_factory=list, max_length=5)
