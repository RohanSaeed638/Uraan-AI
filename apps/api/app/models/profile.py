from datetime import date

from sqlalchemy import Enum
from sqlalchemy import Date, String, Integer, Boolean 
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

    # "user" or "admin": who can open the admin portal.
    role: Mapped[str] = mapped_column(
        String(20),
        default="user",
        server_default="user",
        nullable=False,
    )

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
        server_default="0",
    )

    xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
    )

    last_activity_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Secret in the user's calendar feed URL; regenerating it revokes the
    # old link.
    calendar_token: Mapped[str | None] = mapped_column(
        String(64),
        unique=True,
        nullable=True,
    )

    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    # The database type holds the lowercase values ("job_ready"), not the
    # member names, so map by value.
    career_stage : Mapped[CareerStage | None] = mapped_column(
        Enum(CareerStage, values_callable=lambda e: [m.value for m in e]),
        nullable=True,
    )

    learning_goal : Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Onboarding "About you" / "Your plan" answers. Plain strings, checked
    # against the choice lists in app/schemas/profile.py.
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)

    education: Mapped[str | None] = mapped_column(String(30), nullable=True)

    device: Mapped[str | None] = mapped_column(String(20), nullable=True)

    goal_type: Mapped[str | None] = mapped_column(String(30), nullable=True)

    preferred_study_hours: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    learning_pace: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    weekend_study: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )
