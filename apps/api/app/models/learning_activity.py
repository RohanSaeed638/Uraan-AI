import uuid
from datetime import datetime, timezone

from app.models.base_model import BaseModel
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

class LearningActivity(BaseModel):
    __tablename__ = "learning_activities"

    __table_args__ = (
        UniqueConstraint(
            "profile_id",
            "learning_unit_id",
            name="uq_learning_activity_profile_unit",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # user_id: Mapped[uuid.UUID] = mapped_column(
    #     UUID(as_uuid=True),
    #     nullable=False,
    #     index=True,
    # )
    profile_id: Mapped[UUID] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("profiles.id", ondelete="CASCADE"),
    nullable=False,
    index=True,
    )

    learning_unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "task_learning_units.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    activity_type: Mapped[str] = mapped_column(
        String(50),
        default="learning_unit_completed",
        nullable=False,
    )

    estimated_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )