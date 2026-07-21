# from sqlalchemy import Boolean, Integer, String
# from sqlalchemy.dialects.postgresql import UUID
# from sqlalchemy.orm import Mapped, mapped_column
# import uuid

# from app.db.base import Base


# class Profile(Base):
#     __tablename__ = "profiles"

#     id: Mapped[uuid.UUID] = mapped_column(
#         UUID(as_uuid=True),
#         primary_key=True,
#         default=uuid.uuid4,
#     )

#     full_name: Mapped[str] = mapped_column(String(255))

#     language: Mapped[str] = mapped_column(String(10), default="en")

#     career: Mapped[str | None] = mapped_column(String(100))

#     skill_level: Mapped[str | None] = mapped_column(String(50))

#     daily_hours: Mapped[int | None] = mapped_column(Integer)

#     target_duration: Mapped[int | None] = mapped_column(Integer)

#     learning_style: Mapped[str | None] = mapped_column(String(50))

#     onboarding_completed: Mapped[bool] = mapped_column(
#         Boolean,
#         default=False,
#     )

from sqlalchemy import String, Integer, Boolean 
from sqlalchemy.orm import Mapped, mapped_column 
from app.models.base_model import BaseModel 
from app.models.enums import SkillLevel, LearningStyle
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