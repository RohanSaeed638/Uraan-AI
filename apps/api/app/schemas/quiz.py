from uuid import UUID

from pydantic import BaseModel, Field


class QuizAnswerRequest(BaseModel):
    question_id: UUID
    selected_option: int = Field(ge=0)


class QuizSubmitRequest(BaseModel):
    answers: list[QuizAnswerRequest] = Field(
        min_length=1,
    )


class QuizQuestionResponse(BaseModel):
    id: UUID
    question: str
    options: list[str]
    order: int


class QuizAnswerResult(BaseModel):
    question_id: UUID
    selected_option: int
    correct_option: int
    is_correct: bool
    explanation: str | None = None


class QuizSubmitResponse(BaseModel):
    attempt_id: UUID
    task_id: UUID

    total_questions: int
    correct_answers: int

    score_percentage: float
    passed: bool
    passing_percentage: float

    results: list[QuizAnswerResult]