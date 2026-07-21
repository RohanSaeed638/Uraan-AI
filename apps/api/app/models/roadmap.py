from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel
from app.models.enums import RoadmapStatus


class Roadmap(BaseModel):
    __tablename__ = "roadmaps"

    profile_id: Mapped[str] = mapped_column(
        ForeignKey("profiles.id")
    )

    career_id: Mapped[str] = mapped_column(
        ForeignKey("careers.id")
    )

    status: Mapped[RoadmapStatus]

    # phases = relationship(
    #     "RoadmapPhase",
    #     back_populates="roadmap",
    #     cascade="all, delete-orphan",
    # )