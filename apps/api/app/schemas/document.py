from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

DocumentKind = Literal["resume", "cover_letter", "linkedin_summary"]


class GenerateDocumentRequest(BaseModel):
    kind: DocumentKind
    target_role: str = Field(min_length=2, max_length=120)

    # Free text the user types: education, experience, links, contact.
    details: str | None = Field(default=None, max_length=4000)

    # Pasted job posting, mainly for cover letters.
    job_description: str | None = Field(default=None, max_length=6000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("target_role")
    @classmethod
    def strip_role(cls, value: str):
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Target role is too short")
        return value


class UpdateDocumentRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1, max_length=30000)

    model_config = ConfigDict(extra="forbid")


class DocumentResponse(BaseModel):
    id: UUID
    kind: DocumentKind
    title: str
    target_role: str | None = None
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
