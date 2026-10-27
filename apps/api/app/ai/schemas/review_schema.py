from typing import Literal

from pydantic import BaseModel, Field, field_validator

Priority = Literal["high", "medium", "low"]
Verdict = Literal["needs_work", "solid", "strong"]


class Improvement(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    detail: str = Field(min_length=1, max_length=700)
    priority: Priority = "medium"


class ReviewOutput(BaseModel):
    """What the mentor says about a piece of work."""

    summary: str = Field(min_length=1, max_length=600)
    verdict: Verdict = "solid"
    strengths: list[str] = Field(min_length=1, max_length=6)
    improvements: list[Improvement] = Field(min_length=1, max_length=7)
    next_steps: list[str] = Field(min_length=1, max_length=5)

    @field_validator("strengths", "next_steps")
    @classmethod
    def clean(cls, value: list[str]):
        cleaned = [" ".join(v.split())[:300] for v in value if v and v.strip()]

        if not cleaned:
            raise ValueError("must not be empty")

        return cleaned
