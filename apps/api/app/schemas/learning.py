from uuid import UUID

from pydantic import BaseModel, Field

class ContinueLearningResponse(BaseModel):
    roadmap_id: UUID
    roadmap_title: str

    phase_id: UUID
    phase_title: str

    task_id: UUID
    task_title: str

    learning_unit_id: UUID
    learning_unit_title: str
    learning_unit_type: str

    day: int
    estimated_minutes: int | None = None


class LearningAgendaUnitResponse(BaseModel):
    id: UUID

    roadmap_id: UUID
    task_id: UUID
    task_title: str

    title: str
    type: str
    order: int

    estimated_minutes: int | None = None
    completed: bool


class LearningAgendaDayResponse(BaseModel):
    day: int
    total_estimated_minutes: int
    units: list[LearningAgendaUnitResponse]


class LearningAgendaResponse(BaseModel):
    roadmap_id: UUID | None = None
    roadmap_title: str | None = None

    view: str

    total_units: int = 0
    completed_units: int = 0
    total_estimated_minutes: int = 0

    days: list[LearningAgendaDayResponse] = Field(
        default_factory=list
    )

