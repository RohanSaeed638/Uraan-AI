from sqlalchemy import String, Integer, ForeignKey
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

    roadmap = relationship(
        "Roadmap",
        back_populates="phases"
    )

    tasks = relationship(
        "RoadmapTask",
        back_populates="phase",
        cascade="all, delete-orphan"
    )