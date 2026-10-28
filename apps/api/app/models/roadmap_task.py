from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel
from .resource import Resource

class RoadmapTask(BaseModel):
    __tablename__ = "roadmap_tasks"

    phase_id: Mapped[UUID] = mapped_column(
        ForeignKey("roadmap_phases.id"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    resource_links: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )

    estimated_hours: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # The roadmap week (1 = first) this task is planned for.
    week: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )

    phase = relationship(
        "RoadmapPhase",
        back_populates="tasks",
    )

    learning_units = relationship(
        "TaskLearningUnit",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskLearningUnit.day, TaskLearningUnit.order",
    )

    resources: Mapped[list["Resource"]] = relationship(
    "Resource",
    back_populates="task",
    cascade="all, delete-orphan",
)