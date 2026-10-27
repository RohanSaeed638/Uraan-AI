"""The study planner: puts a learner's unfinished lessons onto calendar days.

A pure function of the lessons, the learner's availability and any lessons they
pinned to a date, so every rule here can be tested exactly. `PlannerService`
(planner_service.py) only gathers the inputs.

Rules
- Lessons keep their order. They fill each study day up to that day's minutes,
  then continue on the next one. A lesson is never split across days.
- Days with 0 minutes (weekends the learner skips, days they blocked, weekdays
  they set to 0) get nothing.
- A lesson longer than a whole day still gets a day to itself.
- A lesson the learner moved (pinned) stays on the date they chose, whatever
  the plan around it does. If that date passes unfinished it is shown as missed.
- Anything not pinned that was due before today is simply planned again from
  today: missed lessons move on by themselves.
- A day's lessons form one block that starts at the learner's preferred time.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from uuid import UUID

DEFAULT_MINUTES = 30
MIN_DAILY_MINUTES = 30
MAX_DAILY_MINUTES = 12 * 60

# How far ahead the plan looks, so an impossible availability cannot loop.
HORIZON_DAYS = 400

LATEST_END = time(23, 30)
EARLIEST_START = time(5, 0)

PART_OF_DAY_START = {
    "morning": time(8, 0),
    "afternoon": time(14, 0),
    "evening": time(19, 0),
    "night": time(21, 0),
}
FALLBACK_START = time(18, 0)


@dataclass
class PlanUnit:
    id: UUID
    task_id: UUID
    task_title: str
    title: str
    type: str
    minutes: int | None
    completed: bool = False

    @property
    def length(self) -> int:
        return max(self.minutes or DEFAULT_MINUTES, 1)


@dataclass
class Availability:
    """Minutes the learner can study on each weekday (Monday = 0), the dates
    they cannot study at all, and when a study day starts."""

    weekday_minutes: list[int]
    blocked: set[date] = field(default_factory=set)
    start: time = FALLBACK_START

    def minutes_on(self, day: date) -> int:
        if day in self.blocked:
            return 0

        return max(self.weekday_minutes[day.weekday()], 0)


@dataclass
class Placed:
    unit: PlanUnit
    start: time
    end: time
    pinned: bool = False
    missed: bool = False


@dataclass
class PlannedDay:
    date: date
    start: time
    end: time
    minutes: int
    placed: list[Placed]


@dataclass
class PlanResult:
    days: list[PlannedDay]
    # Lessons that found no room within the horizon (no study time at all).
    unscheduled: list[PlanUnit]


def clamp_daily_minutes(minutes: int | None) -> int:
    return min(max(minutes or 120, MIN_DAILY_MINUTES), MAX_DAILY_MINUTES)


def start_for(part_of_day: str | None, reminder: time | None = None) -> time:
    """When a study day starts, from the learner's preferred time of day."""
    return PART_OF_DAY_START.get(part_of_day or "") or reminder or FALLBACK_START


def _block_times(start: time, minutes: int) -> tuple[datetime, datetime]:
    """Start and end of a day's block, moved earlier if it would run past the
    latest sensible finish."""
    base = datetime.combine(date(2000, 1, 1), start)
    end = base + timedelta(minutes=minutes)
    limit = datetime.combine(date(2000, 1, 1), LATEST_END)

    if end > limit:
        shift = end - limit
        base = max(base - shift, datetime.combine(date(2000, 1, 1), EARLIEST_START))
        end = base + timedelta(minutes=minutes)

        # A block longer than the whole sensible window runs on from its start.
        if end > limit:
            end = min(end, datetime.combine(date(2000, 1, 1), time(23, 59)))

    return base, end


def _timeline(day: date, start: time, items: list[tuple[PlanUnit, bool, bool]]) -> PlannedDay:
    total = sum(unit.length for unit, _, _ in items)
    block_start, block_end = _block_times(start, total)

    placed = []
    cursor = block_start

    for unit, pinned, missed in items:
        end = cursor + timedelta(minutes=unit.length)
        placed.append(Placed(unit, cursor.time(), min(end, block_end).time(), pinned, missed))
        cursor = end

    return PlannedDay(day, block_start.time(), block_end.time(), total, placed)


def plan(
    units: list[PlanUnit],
    today: date,
    availability: Availability,
    pinned: dict[UUID, date] | None = None,
) -> PlanResult:
    """The plan for the unfinished `units` (given in lesson order)."""
    pinned = pinned or {}
    order = {u.id: i for i, u in enumerate(units)}
    open_units = [u for u in units if not u.completed]

    on_date: dict[date, list[tuple[int, PlanUnit, bool, bool]]] = {}
    pinned_minutes: dict[date, int] = {}

    # 1. Pinned lessons stay where the learner put them.
    for unit in open_units:
        when = pinned.get(unit.id)

        if when is None:
            continue

        missed = when < today
        on_date.setdefault(when, []).append((order[unit.id], unit, True, missed))
        pinned_minutes[when] = pinned_minutes.get(when, 0) + unit.length

    # 2. The rest fill the free minutes from today on, in order.
    loose = [u for u in open_units if u.id not in pinned]
    unscheduled: list[PlanUnit] = []
    index = 0
    day = today

    for _ in range(HORIZON_DAYS):
        if index >= len(loose):
            break

        capacity = availability.minutes_on(day)
        free = capacity - pinned_minutes.get(day, 0)

        if free > 0:
            taken = 0

            while index < len(loose):
                unit = loose[index]
                fits = taken + unit.length <= free
                # Too long for any day: it takes an otherwise empty one.
                oversize = taken == 0 and unit.length > capacity and pinned_minutes.get(day, 0) == 0

                if not (fits or oversize):
                    break

                on_date.setdefault(day, []).append((order[unit.id], unit, False, False))
                taken += unit.length
                index += 1

                if oversize:
                    break

        day += timedelta(days=1)

    unscheduled = loose[index:]

    days = []

    for when in sorted(on_date):
        items = sorted(on_date[when], key=lambda item: item[0])
        days.append(_timeline(when, availability.start, [(u, p, m) for _, u, p, m in items]))

    return PlanResult(days=days, unscheduled=unscheduled)
