from typing import Literal

from pydantic import BaseModel, Field, field_validator

UnitType = Literal["reading", "video", "project", "exercise"]

# What each learning style may contain. Reading is always included.
ALLOWED_TYPES: dict[str, set[str]] = {
    "reading": {"reading"},
    "reading_video": {"reading", "video"},
    "reading_video_project": {"reading", "video", "project"},
}

# Coding exercises are added for coding careers (see allowed_types).
MAX_UNITS = 20
MAX_EXERCISES_PER_TASK = 3
PROJECT_LEVELS = {"beginner", "intermediate", "advanced"}

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

    # Exercises: the programming language (or "bash", "sql").
    language: str | None = None

    # Projects: how hard it is, which skills it practises and why it is worth
    # showing to an employer.
    difficulty: str | None = None
    skills: list[str] = Field(default_factory=list, max_length=8)
    portfolio_value: str | None = None

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


def allowed_types(learning_style, coding: bool = False) -> set[str]:
    """Lesson types for a learner; coding careers also get exercises."""
    allowed = set(ALLOWED_TYPES[style_key(learning_style)])

    if coding:
        allowed.add("exercise")

    return allowed


def style_key(learning_style) -> str:
    value = getattr(learning_style, "value", learning_style)

    return value if value in ALLOWED_TYPES else "reading"


def word_count(text: str | None) -> int:
    return len((text or "").split())


def validate_plan(plan: LearningPlan, learning_style, coding: bool = False) -> None:
    """Raises ValueError when the outline can't be turned into lessons.

    Strict about structure, lenient about timing (a lesson that runs 10
    minutes long is still a good lesson)."""
    allowed = allowed_types(learning_style, coding)
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

    exercises = [u for u in units if u.type == "exercise"]

    if len(exercises) > MAX_EXERCISES_PER_TASK:
        raise ValueError(f"At most {MAX_EXERCISES_PER_TASK} exercises per task")

    if len({u.day for u in exercises}) != len(exercises):
        raise ValueError("At most one exercise per day")

    for unit in units:
        if unit.type == "exercise" and not unit.language:
            raise ValueError(f"Exercise '{unit.title}' needs a language")

        if unit.type in ("reading", "project", "exercise") and len(unit.outline) < 2:
            raise ValueError(f"'{unit.title}' needs an outline of what to cover")

        if unit.type == "video" and not unit.video_urls and not unit.search_query:
            raise ValueError(f"Video '{unit.title}' has no link or search phrase")


def trim_exercises(plan: LearningPlan) -> None:
    """Keeps at most one exercise a day and MAX_EXERCISES_PER_TASK in all.

    The model sometimes over-delivers; dropping the surplus is better than
    throwing the whole plan away. Days left empty are closed up, so the days
    still run 1..n without gaps. Changes the plan in place."""
    kept: list[PlanUnit] = []
    exercise_days: set[int] = set()
    total = 0

    for unit in sorted(plan.units, key=lambda u: (u.day, u.order)):
        if unit.type == "exercise":
            if unit.day in exercise_days or total >= MAX_EXERCISES_PER_TASK:
                continue

            exercise_days.add(unit.day)
            total += 1

        kept.append(unit)

    days = sorted({u.day for u in kept})
    renumber = {day: n for n, day in enumerate(days, start=1)}

    for unit in kept:
        unit.day = renumber[unit.day]

    plan.units = kept


def normalize_order(plan: LearningPlan) -> list[PlanUnit]:
    """Units sorted by day, with order renumbered 1..n inside each day."""
    ordered = sorted(plan.units, key=lambda u: (u.day, u.order))
    counters: dict[int, int] = {}

    for unit in ordered:
        counters[unit.day] = counters.get(unit.day, 0) + 1
        unit.order = counters[unit.day]

    return ordered
