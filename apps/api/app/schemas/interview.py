from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

Difficulty = Literal["beginner", "intermediate", "advanced"]


class StartInterviewRequest(BaseModel):
    role: str = Field(min_length=2, max_length=120)
    difficulty: Difficulty | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("role")
    @classmethod
    def strip_role(cls, value: str):
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Role is too short")
        return value


class AnswerRequest(BaseModel):
    answer: str = Field(min_length=1, max_length=4000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("answer")
    @classmethod
    def strip_answer(cls, value: str):
        value = value.strip()
        if not value:
            raise ValueError("Answer cannot be empty")
        return value


class TurnResponse(BaseModel):
    order: int
    question: str
    answer: str | None = None
    feedback: str | None = None
    technical_score: int | None = None
    communication_score: int | None = None
    confidence_score: int | None = None

    model_config = ConfigDict(from_attributes=True)


class Averages(BaseModel):
    technical: float
    communication: float
    confidence: float


class InterviewSummary(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


class SessionResponse(BaseModel):
    id: UUID
    role: str
    difficulty: str
    status: str
    overall_score: float | None = None
    averages: Averages | None = None
    summary: InterviewSummary | None = None
    answered: int
    total: int
    created_at: datetime
    turns: list[TurnResponse]


class SessionListItem(BaseModel):
    id: UUID
    role: str
    difficulty: str
    status: str
    overall_score: float | None = None
    answered: int
    total: int
    created_at: datetime


class SessionListResponse(BaseModel):
    sessions: list[SessionListItem]
