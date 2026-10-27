from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel


class RoadmapVersion(BaseModel):
    """A saved copy of a roadmap's phases and tasks, taken before the
    roadmap is regenerated, adapted or restored."""

    __tablename__ = "roadmap_versions"
    __table_args__ = (
        UniqueConstraint("roadmap_id", "version_number"),
    )

    roadmap_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("roadmaps.id", ondelete="CASCADE"),
        index=True,
    )

    version_number: Mapped[int] = mapped_column(Integer)

    # regenerate / adapt / restore: what happened right after this copy.
    reason: Mapped[str] = mapped_column(String(20))

    snapshot: Mapped[dict] = mapped_column(JSONB)

    roadmap = relationship("Roadmap", back_populates="versions")
