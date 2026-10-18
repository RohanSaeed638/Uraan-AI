from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class ScheduledUnit(BaseModel):
    id: UUID
    task_id: UUID
    task_title: str
    title: str
    type: str
    estimated_minutes: int | None = None
    completed: bool


class ScheduledDay(BaseModel):
    date: date
    day: int
    total_estimated_minutes: int
    units: list[ScheduledUnit]


class CalendarScheduleResponse(BaseModel):
    roadmap_id: UUID | None = None
    roadmap_title: str | None = None
    today: date
    days: list[ScheduledDay] = Field(default_factory=list)


class CalendarSubscriptionResponse(BaseModel):
    token: str
