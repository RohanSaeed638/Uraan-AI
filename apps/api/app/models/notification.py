import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import BaseModel


class Notification(BaseModel):
    """An in-app notification. `dedupe_key` makes scheduled ones send
    at most once per period (for example per local day)."""

    __tablename__ = "notifications"

    __table_args__ = (
        UniqueConstraint(
            "profile_id",
            "type",
            "dedupe_key",
            name="uq_notification_once",
        ),
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    url: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )

    dedupe_key: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
