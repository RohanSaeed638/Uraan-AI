from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import SkillLevel
from app.models.enums import LearningStyle


class UpdateProfileRequest(BaseModel):

    full_name: str

    language: str

    career_slug: str

    skill_level: SkillLevel

    daily_hours: int

    target_duration: int

    learning_style: LearningStyle

    onboarding_completed: bool


class ProfileResponse(BaseModel):

    id: UUID

    full_name: str

    language: str

    career_slug: str | None

    skill_level: SkillLevel | None

    daily_hours: int

    target_duration: int

    learning_style: LearningStyle | None

    onboarding_completed: bool

    model_config = ConfigDict(from_attributes=True)  