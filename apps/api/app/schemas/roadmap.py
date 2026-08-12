from datetime import datetime
from uuid import UUID

from app.models.enums import LearningStyle, RoadmapStatus, SkillLevel, CareerStage
from pydantic import BaseModel, Field


class TaskResponse(BaseModel):
    id: UUID
    phase_id: UUID
    title: str
    description: str | None
    resource_links: list[str] | None
    estimated_hours: int | None
    order: int
    completed: bool

    class Config:
        from_attributes = True


class PhaseResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    order: int

    tasks: list[TaskResponse]

    class Config:
        from_attributes = True


class RoadmapResponse(BaseModel):
    id: UUID

    title: str

    description: str | None

    status: str

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