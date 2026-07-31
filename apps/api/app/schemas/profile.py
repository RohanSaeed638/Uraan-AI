from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import CareerStage, SkillLevel
from app.models.enums import LearningStyle


class UpdateProfileRequest(BaseModel):

    full_name: str

    language: str

    career_slug: str

    skill_level: SkillLevel

    daily_hours: int

    target_duration: int

    learning_style: LearningStyle

    career_stage: CareerStage | None
    
    learning_goal: str | None

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

    career_stage: CareerStage | None

    learning_goal: str | None

    model_config = ConfigDict(from_attributes=True)  