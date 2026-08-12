from pydantic import BaseModel


class TaskOutput(BaseModel):

    title: str

    description: str

    resource_links: list[str]

    difficulty: str

    estimated_hours: int


class PhaseOutput(BaseModel):

    title: str

    description: str

    order: int

    estimated_weeks: int

    tasks: list[TaskOutput]


class RoadmapOutput(BaseModel):

    title: str

    description: str

    phases: list[PhaseOutput]