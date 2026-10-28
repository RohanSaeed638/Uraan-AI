import uuid

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import BaseModel


class Portfolio(BaseModel):
    """One portfolio per profile. It is private until `is_public` is on."""

    __tablename__ = "portfolios"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    headline: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
    )

    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    slug: Mapped[str | None] = mapped_column(
        String(60),
        unique=True,
        nullable=True,
    )

    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # {"readme": true, ...} for the GitHub checklist.
    checklist: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )


class PortfolioProject(BaseModel):
    __tablename__ = "portfolio_projects"

    __table_args__ = (
        UniqueConstraint(
            "profile_id",
            "source_unit_id",
            name="uq_portfolio_project_source",
        ),
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The roadmap project lesson this entry was created from, if any.
    source_unit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("task_learning_units.id", ondelete="SET NULL"),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    repo_url: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )

    live_url: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )

    tech: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    visible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
