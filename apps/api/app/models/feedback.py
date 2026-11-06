from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import BaseModel

# Why a learner marked a lesson as not helpful.
FEEDBACK_REASONS = ("wrong", "unclear", "too_hard", "too_easy", "broken_link", "other")


class LessonFeedback(BaseModel):
    """One learner's "was this helpful?" on one of their lessons.

    Lessons are written separately for each learner, so a vote belongs to that
    learner's copy; the admin view adds votes up by career and topic. The vote is
    kept (not deleted) if the learner's roadmap is, so quality numbers survive
    people tidying up."""

    __tablename__ = "lesson_feedback"
    __table_args__ = (UniqueConstraint("profile_id", "unit_id", name="uq_lesson_feedback_once"),)

    profile_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        index=True,
    )

    # SET NULL keeps the vote (with the copied details below) when the lesson goes.
    unit_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("task_learning_units.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    helpful: Mapped[bool] = mapped_column(Boolean, index=True)

    reason: Mapped[str | None] = mapped_column(String(20))

    comment: Mapped[str | None] = mapped_column(Text)

    # What the lesson was, copied at the time so the admin view still makes sense later.
    career_slug: Mapped[str | None] = mapped_column(String(100), index=True)
    task_title: Mapped[str | None] = mapped_column(String(255))
    lesson_title: Mapped[str | None] = mapped_column(String(255))
    lesson_type: Mapped[str | None] = mapped_column(String(20))
