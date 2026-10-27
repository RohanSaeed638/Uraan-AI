from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import BaseModel


class LibraryResource(BaseModel):
    """A learning resource anyone can browse (the resource library)."""

    __tablename__ = "library_resources"

    title: Mapped[str] = mapped_column(String(255))

    url: Mapped[str] = mapped_column(String(500), unique=True)

    # course / video / docs / book / practice
    type: Mapped[str] = mapped_column(String(20), index=True)

    provider: Mapped[str | None] = mapped_column(String(120))

    description: Mapped[str | None] = mapped_column(Text)

    is_free: Mapped[bool] = mapped_column(Boolean, default=True)

    difficulty: Mapped[str | None] = mapped_column(String(20))

    # Careers (slugs in data/careers.json) this resource is good for.
    career_slugs: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=list,
        server_default="{}",
    )

    language: Mapped[str] = mapped_column(String(10), default="en", server_default="en")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class ResourceBookmark(BaseModel):
    __tablename__ = "resource_bookmarks"
    __table_args__ = (UniqueConstraint("profile_id", "resource_id"),)

    profile_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        index=True,
    )

    resource_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("library_resources.id", ondelete="CASCADE"),
        index=True,
    )


class ResourceRating(BaseModel):
    __tablename__ = "resource_ratings"
    __table_args__ = (
        UniqueConstraint("profile_id", "resource_id"),
        CheckConstraint("rating between 1 and 5", name="resource_rating_range"),
    )

    profile_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        index=True,
    )

    resource_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("library_resources.id", ondelete="CASCADE"),
        index=True,
    )

    rating: Mapped[int] = mapped_column(SmallInteger)
