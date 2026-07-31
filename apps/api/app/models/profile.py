from sqlalchemy import Enum
from sqlalchemy import String, Integer, Boolean 
from sqlalchemy.orm import Mapped, mapped_column 
from app.models.base_model import BaseModel 
from app.models.enums import SkillLevel, LearningStyle, CareerStage
from uuid import UUID
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

class Profile(BaseModel):
    __tablename__ = "profiles"

    auth_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        unique=True,
        nullable=False,
        index=True,
    )

    full_name: Mapped[str] = mapped_column(String(255))

    language: Mapped[str] = mapped_column(
        String(10),
        default="en",
    )

    country: Mapped[str | None]

    timezone: Mapped[str | None]

    career_slug: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    skill_level: Mapped[SkillLevel | None]

    daily_hours: Mapped[int] = mapped_column(
        Integer,
        default=2,
    )

    target_duration: Mapped[int] = mapped_column(
        Integer,
        default=12,
    )

    learning_style: Mapped[LearningStyle | None]

    streak_days: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    career_stage : Mapped[CareerStage | None] = mapped_column(
        Enum(CareerStage),
        nullable=True,
    )

    learning_goal : Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
