from uuid import UUID

from pydantic import BaseModel, Field


class ProjectResponse(BaseModel):
    id: UUID
    title: str
    description: str | None = None

    roadmap_id: UUID
    roadmap_title: str

    phase_id: UUID
    phase_title: str

    task_id: UUID
    task_title: str

    estimated_minutes: int | None = None
    completed: bool
    day: int

    difficulty: str | None = None
    skills: list[str] = Field(default_factory=list)
    portfolio_value: str | None = None


class ProjectListResponse(BaseModel):
    total: int = 0
    completed: int = 0
    pending: int = 0

    projects: list[ProjectResponse] = Field(
        default_factory=list
    )

class ProjectContextResponse(BaseModel):
    id: UUID
    title: str


class ProjectDetailResponse(BaseModel):
    id: UUID
    title: str
    description: str | None = None

    instructions: str | None = None
    resource_url: str | None = None

    estimated_minutes: int | None = None
    day: int
    completed: bool

    difficulty: str | None = None
    skills: list[str] = Field(default_factory=list)
    portfolio_value: str | None = None

    roadmap: ProjectContextResponse
    phase: ProjectContextResponse
    task: ProjectContextResponse
