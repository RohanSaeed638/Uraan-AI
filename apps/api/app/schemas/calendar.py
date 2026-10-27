from datetime import date, time
from uuid import UUID

from pydantic import BaseModel, Field


class ScheduledUnit(BaseModel):
    id: UUID
    task_id: UUID
    task_title: str
    title: str
    type: str
    minutes: int
    start: time
    end: time
    # Moved by the learner to this date; the plan keeps it there.
    pinned: bool
    # Pinned to a day that has passed and not finished.
    missed: bool
    completed: bool = False


class ScheduledDay(BaseModel):
    date: date
    start: time
    end: time
    minutes: int
    units: list[ScheduledUnit]


class Availability(BaseModel):
    # Minutes of study on each weekday, Monday first.
    weekday_minutes: list[int]
    blocked_dates: list[date]
    start: time


class PlannerPreferences(BaseModel):
    # What the learner told the planner, in their own words.
    note: str | None = None
    active: bool = False


class CalendarScheduleResponse(BaseModel):
    roadmap_id: UUID | None = None
    roadmap_title: str | None = None
    today: date
    days: list[ScheduledDay] = Field(default_factory=list)
    # Lessons that found no room because no day has any study time.
    unscheduled: int = 0
    availability: Availability
    preferences: PlannerPreferences
    # Set after an AI schedule change: what it changed.
    summary: str | None = None


class MoveRequest(BaseModel):
    date: date


class OptimiseRequest(BaseModel):
    request: str = Field(min_length=5, max_length=500)


class CalendarSubscriptionResponse(BaseModel):
    token: str
