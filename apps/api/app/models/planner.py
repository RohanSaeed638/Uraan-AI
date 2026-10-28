from datetime import date, time
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import BaseModel


class ScheduleOverride(BaseModel):
    """A lesson the learner moved to a date of their choosing ("pinned"). It
    stays there; everything else is planned around it."""

    __tablename__ = "schedule_overrides"
    __table_args__ = (UniqueConstraint("profile_id", "unit_id"),)

    profile_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        index=True,
    )

    unit_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("task_learning_units.id", ondelete="CASCADE"),
        index=True,
    )

    date: Mapped[date] = mapped_column(Date)


class SchedulePreference(BaseModel):
    """What the learner told the planner about their time ("exams next week,
    evenings only"), turned into rules by the AI. One row per learner."""

    __tablename__ = "schedule_preferences"

    profile_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        unique=True,
    )

    # {"0": 60, "5": 0}: minutes for some weekdays (Monday is "0").
    weekday_minutes: Mapped[dict] = mapped_column(JSONB, default=dict)

    # ISO dates with no study at all.
    blocked_dates: Mapped[list] = mapped_column(JSONB, default=list)

    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    # The learner's own words, shown back to them.
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class ScheduleSnapshot(BaseModel):
    """Yesterday's plan, so a missed lesson can be noticed and the learner
    told it moved. One row per learner."""

    __tablename__ = "schedule_snapshots"

    profile_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        unique=True,
    )

    # The day the snapshot was taken (the learner's own calendar).
    day: Mapped[date] = mapped_column(Date)

    # {lesson id: planned ISO date}
    plan: Mapped[dict] = mapped_column(JSONB, default=dict)
