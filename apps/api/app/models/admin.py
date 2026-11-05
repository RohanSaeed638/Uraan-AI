import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import BaseModel


class AuditLog(BaseModel):
    """One thing an admin did, kept for good: who, what, to what, and the change."""

    __tablename__ = "audit_logs"

    # No cascade: the record outlives the admin's profile.
    actor_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # The actor's name and email at the time, so the log still reads after a rename.
    actor_label: Mapped[str] = mapped_column(String(300))

    # career.create, resource.update, announcement.publish, user.role...
    action: Mapped[str] = mapped_column(String(60), index=True)

    target_type: Mapped[str] = mapped_column(String(40))

    target_id: Mapped[str | None] = mapped_column(String(100))

    summary: Mapped[str] = mapped_column(String(300))

    # What changed: {"field": [before, after]}.
    changes: Mapped[dict | None] = mapped_column(JSONB)


class Announcement(BaseModel):
    """A message for every learner: a banner in the app, and optionally a notification."""

    __tablename__ = "announcements"

    title: Mapped[str] = mapped_column(String(160))

    body: Mapped[str] = mapped_column(Text)

    # info or warning: only changes the colour of the banner.
    level: Mapped[str] = mapped_column(String(20), default="info", server_default="info")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # How many learners were sent a notification when it was published.
    notified: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
