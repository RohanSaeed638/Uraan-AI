import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import BaseModel


class InterviewSession(BaseModel):
    __tablename__ = "interview_sessions"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    difficulty: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="in_progress",
        server_default="in_progress",
    )

    # 0 to 100, set when the session is finished.
    overall_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # {"strengths": [...], "improvements": [...], "next_steps": [...]}
    summary: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )


class InterviewTurn(BaseModel):
    """One question and, once answered, its scored feedback."""

    __tablename__ = "interview_turns"

    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "order",
            name="uq_interview_turn_order",
        ),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    answer: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    technical_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    communication_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    answered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
