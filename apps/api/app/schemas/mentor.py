from datetime import date, datetime
from uuid import UUID

from typing import Literal

from pydantic import BaseModel, Field, model_validator

class MentorConversationCreateRequest(BaseModel):
    title: str = Field(
        default="New Conversation",
        min_length=1,
        max_length=200,
    )

class MentorConversationResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }

class MentorConversationListResponse(BaseModel):
    conversations: list[MentorConversationResponse] = Field(
        default_factory=list
    )

    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool    

class MentorMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }

class MentorConversationDetailResponse(
    MentorConversationResponse
):
    messages: list[MentorMessageResponse] = Field(
        default_factory=list
    )    

class MentorMessageCreateRequest(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=8000,
    )

class MentorMessageCreateResponse(BaseModel):
    conversation_id: UUID
    user_message: MentorMessageResponse
    assistant_message: MentorMessageResponse    


class MentorChip(BaseModel):
    id: str
    label: str
    # "ask": send `prompt` as a message. "review": open the code review panel.
    kind: str
    prompt: str | None = None


class MentorSuggestionsResponse(BaseModel):
    chips: list[MentorChip]


class ReviewRequest(BaseModel):
    """Ask the mentor to review some work."""

    kind: Literal["github", "code", "portfolio"]
    url: str | None = Field(default=None, max_length=300)
    code: str | None = Field(default=None, max_length=20000)
    language: str | None = Field(default=None, max_length=30)
    note: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def needs_its_input(self):
        if self.kind == "github" and not (self.url or "").strip():
            raise ValueError("Paste a GitHub link to review.")

        if self.kind == "code" and len((self.code or "").strip()) < 20:
            raise ValueError("Paste some code to review (at least a few lines).")

        return self


class ReviewImprovement(BaseModel):
    title: str
    detail: str
    priority: str


class ReviewResponse(BaseModel):
    kind: str
    reviewed: str
    summary: str
    verdict: str
    strengths: list[str]
    improvements: list[ReviewImprovement]
    next_steps: list[str]


class MotivationResponse(BaseModel):
    message: str
    day: date
    # "ai" or "fallback" (a plain message, used when the AI could not answer).
    source: str
