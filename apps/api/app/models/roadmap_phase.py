from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel


class RoadmapPhase(BaseModel):
    __tablename__ = "roadmap_phases"

    roadmap_id: Mapped[str] = mapped_column(
        ForeignKey("roadmaps.id")
    )

    order: Mapped[int]

    title: Mapped[str] = mapped_column(
        String(255)
    )

    description: Mapped[str] = mapped_column(
        String(1000)
    )

    duration_weeks: Mapped[int]

    # What the learner can do by the end of the phase (2-4 short lines).
    milestones: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )

    roadmap = relationship(
        "Roadmap",
        back_populates="phases"
    )

    tasks = relationship(
        "RoadmapTask",
        back_populates="phase",
        cascade="all, delete-orphan",
        order_by="RoadmapTask.order",
    )