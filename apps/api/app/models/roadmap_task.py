from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel

class RoadmapTask(BaseModel):

    __tablename__ = "roadmap_tasks"

    phase_id: Mapped[UUID] = mapped_column(
        ForeignKey("roadmap_phases.id")
    )

    title: Mapped[str] = mapped_column(
        String(255)
    )

    description: Mapped[str | None]

    resource_url: Mapped[str | None]

    estimated_hours: Mapped[int | None]

    order: Mapped[int] = mapped_column(
        Integer
    )

    completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    phase = relationship(
        "RoadmapPhase",
        back_populates="tasks",
    )    