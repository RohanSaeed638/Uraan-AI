from datetime import datetime
from uuid import UUID

from app.models.enums import RoadmapStatus
from pydantic import BaseModel


class TaskResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    estimated_hours: int | None
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