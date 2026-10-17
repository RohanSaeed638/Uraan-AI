from uuid import UUID

from pydantic import BaseModel


class DashboardUserResponse(BaseModel):
    name: str | None = None
    career_goal: str | None = None


class DashboardRoadmapResponse(BaseModel):
    id: UUID
    title: str
    total_phases: int
    total_tasks: int
    completed_tasks: int
    completion_percentage: float


class DashboardNextLearningResponse(BaseModel):
    roadmap_id: UUID
    task_id: UUID
    learning_unit_id: UUID

    task_title: str
    learning_unit_title: str
    learning_unit_type: str
    estimated_minutes: int | None = None


class DashboardStatsResponse(BaseModel):
    total_roadmaps: int = 0
    completed_roadmaps: int = 0

    total_tasks: int = 0
    completed_tasks: int = 0
    remaining_tasks: int = 0

    total_learning_units: int = 0
    completed_learning_units: int = 0


class DashboardSummaryResponse(BaseModel):
    user: DashboardUserResponse
    current_roadmap: DashboardRoadmapResponse | None = None
    next_learning: DashboardNextLearningResponse | None = None
    stats: DashboardStatsResponse