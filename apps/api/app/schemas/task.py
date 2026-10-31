from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator
from app.models.task_learning_unit import LearningUnitType

class LearningUnitResponse(BaseModel):
    id: UUID
    task_id: UUID

    day: int
    order: int

    type: LearningUnitType

    title: str

    description: str | None = None

    content: str | None = None

    resource_url: str | None = None

    # Exercise: language, starter_code, hints, solution. Project: difficulty,
    # skills, portfolio_value.
    details: dict | None = None

    estimated_minutes: int | None = None

    # ready, pending, writing or failed: the lesson text is filled in behind the plan.
    status: str = "ready"

    completed: bool

    model_config = ConfigDict(
        from_attributes=True
    )

    @field_validator("details")
    @classmethod
    def hide_internal(cls, value):
        """Keys starting with "_" (the saved outline of a lesson still being
        written) are for the server, not the learner."""
        if isinstance(value, dict):
            return {k: v for k, v in value.items() if not k.startswith("_")} or None

        return value

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
    learning_units: list[LearningUnitResponse] = []

class UpdateTaskCompletionRequest(BaseModel):
    completed: bool


class RoadmapProgressResponse(BaseModel):
    total: int
    completed: int

class TaskListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    phase_id: UUID
    title: str
    description: str | None = None
    estimated_hours: float | None = None
    order: int
    completed: bool
