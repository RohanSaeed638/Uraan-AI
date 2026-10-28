import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import BaseModel


class PushSubscription(BaseModel):
    """A browser or device that can receive web push for a profile."""

    __tablename__ = "push_subscriptions"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    endpoint: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
    )

    p256dh: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    auth: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
