from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel


class Career(BaseModel):
    __tablename__ = "careers"

    name: Mapped[str] = mapped_column(String(200))

    slug: Mapped[str] = mapped_column(
        String(200),
        unique=True,
    )

    description: Mapped[str] = mapped_column(Text())

    icon: Mapped[str | None]

    category: Mapped[str | None]

    # beginner / intermediate / advanced: how hard it is to break in.
    difficulty: Mapped[str | None] = mapped_column(String(20))

    estimated_months: Mapped[int | None] = mapped_column(Integer)

    # Monthly salary range in PKR (entry level to experienced).
    salary_min_pkr: Mapped[int | None] = mapped_column(Integer)

    salary_max_pkr: Mapped[int | None] = mapped_column(Integer)

    # low / medium / high / very_high
    market_demand: Mapped[str | None] = mapped_column(String(20))

    color: Mapped[str | None] = mapped_column(String(20))

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
    )

    skills: Mapped[list["CareerSkill"]] = relationship(
        back_populates="career",
        order_by="CareerSkill.order_number",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    resources: Mapped[list["CareerResource"]] = relationship(
        back_populates="career",
        order_by="CareerResource.order_number",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CareerSkill(BaseModel):
    __tablename__ = "career_skills"

    career_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("careers.id", ondelete="CASCADE"),
        index=True,
    )

    name: Mapped[str] = mapped_column(String(120))

    order_number: Mapped[int] = mapped_column(Integer, default=0)

    career: Mapped[Career] = relationship(back_populates="skills")


class CareerResource(BaseModel):
    __tablename__ = "career_resources"

    career_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("careers.id", ondelete="CASCADE"),
        index=True,
    )

    title: Mapped[str] = mapped_column(String(255))

    # course / video / docs / book / practice
    type: Mapped[str] = mapped_column(String(20))

    provider: Mapped[str | None] = mapped_column(String(120))

    url: Mapped[str] = mapped_column(String(500))

    is_free: Mapped[bool] = mapped_column(Boolean, default=True)

    difficulty: Mapped[str | None] = mapped_column(String(20))

    order_number: Mapped[int] = mapped_column(Integer, default=0)

    career: Mapped[Career] = relationship(back_populates="resources")
