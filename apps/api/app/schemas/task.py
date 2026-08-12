from uuid import UUID
from pydantic import BaseModel, ConfigDict

class RoadmapTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    phase_id: UUID
    title: str
    description: str | None
    resource_links: list[str] | None
    estimated_hours: int | None
    order: int
    completed: bool


class UpdateTaskCompletionRequest(BaseModel):
    completed: bool


class RoadmapProgressResponse(BaseModel):
    total: int
    completed: int