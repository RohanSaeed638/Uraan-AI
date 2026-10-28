import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import BaseModel


class XPEvent(BaseModel):
    """One XP award. The unique key makes each award happen only once."""

    __tablename__ = "xp_events"

    __table_args__ = (
        UniqueConstraint(
            "profile_id",
            "reason",
            "ref_id",
            name="uq_xp_event_once",
        ),
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    reason: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    ref_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
