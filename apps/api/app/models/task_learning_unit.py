from uuid import UUID
from enum import Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel


class LearningUnitType(str, Enum):
    READING = "reading"
    VIDEO = "video"
    PROJECT = "project"
    EXERCISE = "exercise"


class TaskLearningUnit(BaseModel):
    __tablename__ = "task_learning_units"

    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("roadmap_tasks.id", ondelete="CASCADE"),
        nullable=False,
    )

    day: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    type: Mapped[LearningUnitType] = mapped_column(
        SQLAlchemyEnum(
            LearningUnitType,
            name="learning_unit_type",
            values_callable=lambda enum_cls: [
                member.value for member in enum_cls
            ],
        ),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Type-specific data. Exercise: {language, problem, starter_code, hints,
    # solution}. Project: {difficulty, skills, portfolio_value}.
    details: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    resource_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    estimated_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )

    task = relationship(
        "RoadmapTask",
        back_populates="learning_units",
    )

    # Which prompt version produced this (see app/ai/versions.py).
    prompt_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
