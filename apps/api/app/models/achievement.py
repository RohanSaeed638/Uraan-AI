from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import BaseModel


class Achievement(BaseModel):
    """A badge anyone can earn. The definitions live in
    app/core/achievement_catalog.py and are copied here on first use."""

    __tablename__ = "achievements"

    code: Mapped[str] = mapped_column(String(40), unique=True)

    title: Mapped[str] = mapped_column(String(100))

    description: Mapped[str] = mapped_column(Text)

    # learning, streak, projects, practice, career
    category: Mapped[str] = mapped_column(String(20))

    # A lucide icon name the web app knows.
    icon: Mapped[str] = mapped_column(String(30))

    xp_reward: Mapped[int] = mapped_column(Integer)

    # What is measured (a key of the learner stats) and the amount that earns it.
    rule: Mapped[str] = mapped_column(String(30))

    threshold: Mapped[int] = mapped_column(Integer)

    position: Mapped[int] = mapped_column(Integer, default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class UserAchievement(BaseModel):
    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("profile_id", "achievement_id"),)

    profile_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        index=True,
    )

    achievement_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("achievements.id", ondelete="CASCADE"),
        index=True,
    )

    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class BossChallenge(BaseModel):
    """The month's boss project: one pending project lesson picked for the
    learner, worth bonus XP if it is finished in the same month."""

    __tablename__ = "boss_challenges"
    __table_args__ = (UniqueConstraint("profile_id", "month"),)

    profile_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        index=True,
    )

    # "2026-10" in the learner's own calendar.
    month: Mapped[str] = mapped_column(String(7))

    unit_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("task_learning_units.id", ondelete="CASCADE"),
    )

    bonus_xp: Mapped[int] = mapped_column(Integer)

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
