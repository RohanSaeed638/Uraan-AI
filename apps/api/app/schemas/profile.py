from datetime import datetime
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.ai.prompts.language import SUPPORTED
from app.core.career_catalog import catalog_slugs
from app.models.enums import CareerStage, SkillLevel
from app.models.enums import LearningStyle

# The slugs of data/careers.json, so validation cannot drift from the catalogue.
CAREER_SLUGS = catalog_slugs()

LANGUAGES = set(SUPPORTED)

Education = Literal["school", "college", "bachelors", "masters", "self_taught", "other"]
Device = Literal["laptop", "desktop", "mobile"]
GoalType = Literal["local_job", "remote_job", "freelancing", "startup", "study_abroad"]
StudyHours = Literal["morning", "afternoon", "evening", "night", "flexible"]
Pace = Literal["relaxed", "steady", "intensive"]

_NEW_CHOICES = (
    "education", "device", "goal_type", "preferred_study_hours", "learning_pace",
)


def _check_timezone(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip()

    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError("Invalid IANA timezone")

    return value


def _lower_choice(value):
    """Accepts 'READING_VIDEO' as well as 'reading_video'."""
    return value.strip().lower() if isinstance(value, str) else value


class UpdateProfileRequest(BaseModel):
    """The onboarding save: every core field at once."""

    full_name: str

    language: str

    career_slug: str

    skill_level: SkillLevel

    daily_hours: int

    target_duration: int

    learning_style: LearningStyle

    career_stage: CareerStage | None = None

    learning_goal: str | None = None

    age: int | None = Field(default=None, ge=10, le=100)

    education: Education | None = None

    device: Device | None = None

    goal_type: GoalType | None = None

    preferred_study_hours: StudyHours | None = None

    learning_pace: Pace | None = None

    weekend_study: bool | None = None

    onboarding_completed: bool

    @field_validator(
        "learning_style", "skill_level", "career_stage", *_NEW_CHOICES,
        mode="before",
    )
    @classmethod
    def lower_enums(cls, value):
        return _lower_choice(value)


class PatchProfileRequest(BaseModel):
    """Edit one or more profile fields; anything left out is unchanged."""

    full_name: str | None = Field(default=None, min_length=1, max_length=100)
    language: str | None = None
    country: str | None = Field(default=None, max_length=60)
    timezone: str | None = None
    career_slug: str | None = None
    skill_level: SkillLevel | None = None
    learning_style: LearningStyle | None = None
    career_stage: CareerStage | None = None
    daily_hours: int | None = Field(default=None, ge=1, le=12)
    target_duration: int | None = Field(default=None, ge=1, le=36)
    learning_goal: str | None = Field(default=None, max_length=255)
    age: int | None = Field(default=None, ge=10, le=100)
    education: Education | None = None
    device: Device | None = None
    goal_type: GoalType | None = None
    preferred_study_hours: StudyHours | None = None
    learning_pace: Pace | None = None
    weekend_study: bool | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("full_name")
    @classmethod
    def strip_name(cls, value):
        if value is None:
            return value

        value = " ".join(value.split())

        if not value:
            raise ValueError("Name cannot be empty")

        return value

    @field_validator("language")
    @classmethod
    def known_language(cls, value):
        if value is not None and value not in LANGUAGES:
            raise ValueError("Unsupported language")

        return value

    @field_validator("career_slug")
    @classmethod
    def known_career(cls, value):
        if value is not None and value not in CAREER_SLUGS:
            raise ValueError("Unknown career path")

        return value

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value):
        return _check_timezone(value)

    @field_validator("country", "learning_goal")
    @classmethod
    def trim_text(cls, value):
        if value is None:
            return value

        return value.strip() or None

    @field_validator(
        "learning_style", "skill_level", "career_stage", *_NEW_CHOICES,
        mode="before",
    )
    @classmethod
    def lower_enums(cls, value):
        return _lower_choice(value)


# Fields that cannot be cleared by sending null.
REQUIRED_PROFILE_FIELDS = {
    "full_name",
    "language",
    "career_slug",
    "skill_level",
    "learning_style",
    "daily_hours",
    "target_duration",
}


class ProfileResponse(BaseModel):

    id: UUID

    full_name: str

    language: str

    country: str | None = None

    timezone: str | None = None

    career_slug: str | None

    skill_level: SkillLevel | None

    daily_hours: int

    target_duration: int

    learning_style: LearningStyle | None

    onboarding_completed: bool

    career_stage: CareerStage | None

    learning_goal: str | None

    age: int | None = None

    education: str | None = None

    device: str | None = None

    goal_type: str | None = None

    preferred_study_hours: str | None = None

    learning_pace: str | None = None

    weekend_study: bool | None = None

    streak_days: int = 0

    xp: int = 0

    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
