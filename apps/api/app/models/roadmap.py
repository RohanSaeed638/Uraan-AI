from enum import Enum

from app.models.enums import CareerStage, LearningStyle, RoadmapStatus, SkillLevel
from sqlalchemy import String, ForeignKey, Integer, Enum as SQLAlchemyEnum
from sqlalchemy import select
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from app.models.profile import Profile

from app.models.base_model import BaseModel


class Roadmap(BaseModel):
    __tablename__ = "roadmaps"

    profile_id: Mapped[str] = mapped_column(
        ForeignKey("profiles.id")
    )

    # Supabase auth user that owns the roadmap, via its profile. Lets queries
    # filter on `Roadmap.user_id == current_user.id`; never loaded onto
    # instances.
    user_id = column_property(
        select(Profile.auth_user_id)
        .where(Profile.id == profile_id)
        .scalar_subquery(),
        deferred=True,
    )

    title: Mapped[str] = mapped_column(
        String(255)
    )

    description: Mapped[str] = mapped_column(
        String(1000)
    )

    # status: Mapped[RoadmapStatus] = mapped_column(
    # SQLAlchemyEnum(
    #     RoadmapStatus,
    #     name="roadmap_status",
    # ),
    # default=RoadmapStatus.GENERATING,
    # nullable=False,
    # )

    status: Mapped[RoadmapStatus] = mapped_column(
    SQLAlchemyEnum(
        RoadmapStatus,
        name="roadmap_status",
        values_callable=lambda enum_cls: [
            member.value for member in enum_cls
        ],
    ),
    nullable=False,
    default=RoadmapStatus.GENERATING,
    server_default="pending",
    )

    career_slug: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
    )

    career_stage: Mapped[CareerStage] = mapped_column(
        SQLAlchemyEnum(
            CareerStage
            ,name="career_stage"
        ),
        nullable=True,
    )

    skill_level: Mapped[SkillLevel] = mapped_column(
    SQLAlchemyEnum(
        SkillLevel,
        name="skill_level",
    ),
    nullable=False,
    )

    learning_goal: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    learning_style: Mapped[LearningStyle] = mapped_column(
    SQLAlchemyEnum(
        LearningStyle,
        name="learning_style",
    ),
    nullable=False,
    )

    daily_hours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    target_duration: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Why the last background generation / regeneration / adaptation failed
    # (a safe, readable message); cleared when one succeeds.
    generation_error: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # The status to go back to if a regeneration or adaptation fails or goes
    # stale; empty for a first generation (which then becomes "failed").
    status_before_job: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # Without an explicit order the database may return rows in any order,
    # which changes after rows are updated.
    phases = relationship(
        "RoadmapPhase",
        back_populates="roadmap",
        cascade="all, delete-orphan",
        order_by="RoadmapPhase.order",
    )    

    versions = relationship(
        "RoadmapVersion",
        back_populates="roadmap",
        cascade="all, delete-orphan",
        order_by="RoadmapVersion.version_number.desc()",
    )

    # Which prompt version produced this (see app/ai/versions.py).
    prompt_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
