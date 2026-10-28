from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import BaseModel


class DailyMotivation(BaseModel):
    """Today's motivational message for a learner, written once a day from
    their real progress and then reused."""

    __tablename__ = "daily_motivations"
    __table_args__ = (UniqueConstraint("profile_id", "day"),)

    profile_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        index=True,
    )

    # The learner's own calendar day (their timezone).
    day: Mapped[date] = mapped_column(Date)

    message: Mapped[str] = mapped_column(Text)

    # "ai" or "fallback" (a plain message used when the AI could not answer).
    source: Mapped[str] = mapped_column(String(10), default="ai")

    prompt_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
