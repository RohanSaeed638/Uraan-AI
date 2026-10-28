"""The AI's reading of "I am free evenings and have exams next week", checked
before it becomes planner rules."""
from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, Field, field_validator

WEEKDAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
MAX_MINUTES = 720
MAX_BLOCKED = 60
HORIZON_DAYS = 120

PartOfDay = Literal["morning", "afternoon", "evening", "night"]


class PlannerRules(BaseModel):
    weekday_minutes: dict[str, int | None] = Field(default_factory=dict)
    blocked_dates: list[str] = Field(default_factory=list)
    start: PartOfDay | None = None
    summary: str = Field(min_length=1, max_length=400)

    @field_validator("weekday_minutes")
    @classmethod
    def valid_weekdays(cls, value: dict):
        clean: dict[str, int | None] = {}

        for key, minutes in value.items():
            key = str(key).strip().lower()[:3]

            if key not in WEEKDAY_KEYS:
                continue

            if minutes is None:
                clean[key] = None
            else:
                clean[key] = min(max(int(minutes), 0), MAX_MINUTES)

        return clean

    def rules_for(self, today: date) -> tuple[dict[str, int], list[str]]:
        """({"0": minutes} for the weekdays that change, the blocked ISO dates
        that are real, in range and unique)."""
        weekday = {
            str(WEEKDAY_KEYS.index(key)): minutes
            for key, minutes in self.weekday_minutes.items()
            if minutes is not None
        }

        last = today + timedelta(days=HORIZON_DAYS)
        blocked: list[str] = []

        for raw in self.blocked_dates:
            try:
                day = date.fromisoformat(str(raw).strip())
            except ValueError:
                continue

            if today <= day <= last and day.isoformat() not in blocked:
                blocked.append(day.isoformat())

        return weekday, sorted(blocked)[:MAX_BLOCKED]
