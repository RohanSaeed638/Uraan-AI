from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel


class Roadmap(BaseModel):
    __tablename__ = "roadmaps"

    profile_id: Mapped[str] = mapped_column(
        ForeignKey("profiles.id")
    )

    title: Mapped[str] = mapped_column(
        String(255)
    )

    description: Mapped[str] = mapped_column(
        String(1000)
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="completed",
    )
    
    phases = relationship(
        "RoadmapPhase",
        back_populates="roadmap",
        cascade="all, delete-orphan"
    )    
