from uuid import UUID

from pydantic import BaseModel, Field


class PhaseProgressResponse(BaseModel):
    phase_id: UUID
    title: str
    total_tasks: int
    completed_tasks: int
    completion_percentage: float = Field(ge=0, le=100)


class RoadmapProgressResponse(BaseModel):
    roadmap_id: UUID

    total_phases: int

    total_tasks: int
    completed_tasks: int
    remaining_tasks: int
    completion_percentage: float = Field(ge=0, le=100)

    total_learning_units: int
    completed_learning_units: int
    learning_completion_percentage: float = Field(ge=0, le=100)

    phases: list[PhaseProgressResponse]

class RoadmapCountStats(BaseModel):
    total: int = 0
    completed: int = 0
    in_progress: int = 0


class CompletionStats(BaseModel):
    total: int = 0
    completed: int = 0
    remaining: int = 0
    completion_percentage: float = Field(
        default=0,
        ge=0,
        le=100,
    )


class RoadmapProgressItem(BaseModel):
    roadmap_id: UUID
    title: str

    total_tasks: int
    completed_tasks: int
    completion_percentage: float


class ProgressOverviewResponse(BaseModel):
    roadmaps: RoadmapCountStats
    tasks: CompletionStats
    learning_units: CompletionStats

    estimated_completed_learning_hours: float = 0

    roadmap_progress: list[RoadmapProgressItem] = Field(
        default_factory=list
    )    