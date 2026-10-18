from typing import Literal

from pydantic import BaseModel, Field, field_validator

UnitType = Literal["reading", "video", "project"]

# What each learning style may contain. Reading is always included.
ALLOWED_TYPES: dict[str, set[str]] = {
    "reading": {"reading"},
    "reading_video": {"reading", "video"},
    "reading_video_project": {"reading", "video", "project"},
}

MAX_UNITS = 20

# A written lesson shorter than this is sent back once for expansion; below
# the floor after that it is rejected.
READING_TARGET_WORDS = 250
READING_FLOOR_WORDS = 180
PROJECT_TARGET_WORDS = 150
PROJECT_FLOOR_WORDS = 100


class PlanUnit(BaseModel):
    """One lesson in the outline. Reading and project bodies are written in
    a second step, from `outline`."""

    day: int = Field(ge=1, le=60)
    order: int = Field(default=1, ge=1)
    type: UnitType
    title: str = Field(min_length=1)
    description: str = Field(default="")

    # What the lesson must cover (reading and project lessons).
    outline: list[str] = Field(default_factory=list, max_length=10)

    # Video lessons: a few lines of notes to follow along with.
    notes: str | None = None

    # Video lessons: candidate YouTube links to verify, plus a search phrase
    # used when none of them exist.
    video_urls: list[str] = Field(default_factory=list, max_length=4)
    search_query: str | None = None

    estimated_minutes: int = Field(ge=1, le=240)

    @field_validator("title", "description")
    @classmethod
    def trim(cls, value: str):
        return value.strip()

    @field_validator("outline")
    @classmethod
    def clean_outline(cls, value: list[str]):
        return [point.strip() for point in value if point and point.strip()]


class LearningPlan(BaseModel):
    units: list[PlanUnit] = Field(min_length=1, max_length=MAX_UNITS)


def style_key(learning_style) -> str:
    value = getattr(learning_style, "value", learning_style)

    return value if value in ALLOWED_TYPES else "reading"


def word_count(text: str | None) -> int:
    return len((text or "").split())


def validate_plan(plan: LearningPlan, learning_style) -> None:
    """Raises ValueError when the outline can't be turned into lessons.

    Strict about structure, lenient about timing (a lesson that runs 10
    minutes long is still a good lesson)."""
    allowed = ALLOWED_TYPES[style_key(learning_style)]
    units = plan.units

    wrong = {u.type for u in units} - allowed
    if wrong:
        raise ValueError(f"Types not allowed for this learner: {sorted(wrong)}")

    if not any(u.type == "reading" for u in units):
        raise ValueError("Plan needs at least one reading lesson")

    days = sorted({u.day for u in units})
    if days != list(range(1, len(days) + 1)):
        raise ValueError("Days must start at 1 and have no gaps")

    if sum(1 for u in units if u.type == "project") > 1:
        raise ValueError("At most one project per task")

    for unit in units:
        if unit.type in ("reading", "project") and len(unit.outline) < 2:
            raise ValueError(f"'{unit.title}' needs an outline of what to cover")

        if unit.type == "video" and not unit.video_urls and not unit.search_query:
            raise ValueError(f"Video '{unit.title}' has no link or search phrase")


def normalize_order(plan: LearningPlan) -> list[PlanUnit]:
    """Units sorted by day, with order renumbered 1..n inside each day."""
    ordered = sorted(plan.units, key=lambda u: (u.day, u.order))
    counters: dict[int, int] = {}

    for unit in ordered:
        counters[unit.day] = counters.get(unit.day, 0) + 1
        unit.order = counters[unit.day]

    return ordered
