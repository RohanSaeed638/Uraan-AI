from uuid import UUID

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