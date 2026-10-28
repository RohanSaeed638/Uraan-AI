from uuid import UUID

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import BaseModel


class AiRequest(BaseModel):
    """One call to an AI provider, kept for usage, latency and failure stats.

    No foreign key on purpose: the log outlives the learner it was made for.
    """

    __tablename__ = "ai_requests"

    profile_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    # roadmap, lessons, quiz, mentor, review, motivation...
    purpose: Mapped[str] = mapped_column(String(40), index=True)

    prompt_version: Mapped[str | None] = mapped_column(String(40))

    provider: Mapped[str] = mapped_column(String(20))

    model: Mapped[str] = mapped_column(String(80))

    success: Mapped[bool] = mapped_column(Boolean)

    # The exception class on failure (never its message: it can hold secrets).
    error_type: Mapped[str | None] = mapped_column(String(80))

    latency_ms: Mapped[int | None] = mapped_column(Integer)

    input_tokens: Mapped[int | None] = mapped_column(Integer)

    output_tokens: Mapped[int | None] = mapped_column(Integer)
