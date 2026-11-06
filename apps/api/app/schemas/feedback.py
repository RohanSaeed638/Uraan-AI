from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Reason = Literal["wrong", "unclear", "too_hard", "too_easy", "broken_link", "other"]


class FeedbackRequest(BaseModel):
    helpful: bool
    # Only kept for "not helpful".
    reason: Reason | None = None
    comment: str | None = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="forbid")


class FeedbackResponse(BaseModel):
    helpful: bool
    reason: Reason | None = None
    comment: str | None = None
