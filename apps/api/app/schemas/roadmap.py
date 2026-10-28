from datetime import datetime
from typing import Literal
from uuid import UUID

from app.models.enums import LearningStyle, RoadmapStatus, SkillLevel, CareerStage
from app.schemas.task import LearningUnitResponse
from pydantic import BaseModel, Field, ConfigDict
from app.models.task_learning_unit import LearningUnitType

class TaskResponse(BaseModel):
    id: UUID
    phase_id: UUID
    title: str
    description: str | None
    resource_links: list[str] | None
    estimated_hours: int | None
    order: int
    completed: bool
    week: int | None = None
    learning_units: list[LearningUnitResponse] = []
    
    class Config:
        from_attributes = True


class PhaseResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    order: int
    duration_weeks: int | None = None
    milestones: list[str] | None = None

    tasks: list[TaskResponse]

    class Config:
        from_attributes = True


class RoadmapResponse(BaseModel):
    id: UUID

    title: str

    description: str | None

    status: str

    generation_error: str | None = None

    daily_hours: int | None = None

    target_duration: int | None = None

    phases: list[PhaseResponse]

    class Config:
        from_attributes = True

class UpdateTaskRequest(BaseModel):
    completed: bool        


class RoadmapSummaryResponse(BaseModel):

    id: UUID

    title: str

    description: str

    status: RoadmapStatus

    progress: int

    completed_tasks: int

    total_tasks: int

    updated_at: datetime

    model_config = {
        "from_attributes": True
    }    

class RoadmapGenerateRequest(BaseModel):
    career_slug: str = Field(min_length=1, max_length=100)

    career_stage: CareerStage

    skill_level: SkillLevel

    learning_goal: str = Field(
        min_length=1,
        max_length=255,
    )

    daily_hours: int = Field(
        gt=0,
        le=24,
    )

    target_duration: int = Field(
        gt=0,
        le=60,
    )

    learning_style: LearningStyle    

class UpdateLearningUnitRequest(BaseModel):
    completed: bool


class RoadmapActivateResponse(BaseModel):
    id: UUID
    title: str
    status: RoadmapStatus
    message: str


class RoadmapStatusResponse(BaseModel):
    """What the browser polls while a roadmap is being built or rebuilt."""

    id: UUID
    title: str
    status: RoadmapStatus
    error: str | None = None


class AdaptRequest(BaseModel):
    """Re-plan the unfinished part of a roadmap."""

    reason: Literal["study_time", "behind", "goal"]

    # New study time per day, and months the remaining plan should take.
    daily_hours: int | None = Field(default=None, ge=1, le=12)
    months_left: int | None = Field(default=None, ge=1, le=36)

    note: str | None = Field(default=None, max_length=300)


class RoadmapVersionResponse(BaseModel):
    id: UUID
    version_number: int
    reason: str
    created_at: datetime
    phases: int
    tasks: int
    completed: int
