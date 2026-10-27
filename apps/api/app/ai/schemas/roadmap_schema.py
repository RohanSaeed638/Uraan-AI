from pydantic import BaseModel


class TaskOutput(BaseModel):

    title: str

    description: str

    resource_links: list[str]

    difficulty: str

    estimated_hours: int

    week: int | None = None


class PhaseOutput(BaseModel):

    title: str

    description: str

    order: int

    estimated_weeks: int

    milestones: list[str] = []

    tasks: list[TaskOutput]


class RoadmapOutput(BaseModel):

    title: str

    description: str

    phases: list[PhaseOutput]

class LearningUnitOutput(BaseModel):
    day: int
    order: int
    type: str
    title: str
    description: str
    content: str | None = None
    resource_url: str | None = None
    estimated_minutes: int

class TaskLearningPlanOutput(BaseModel):
    learning_units: list[LearningUnitOutput]
      