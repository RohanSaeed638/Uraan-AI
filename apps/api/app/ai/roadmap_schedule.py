"""Puts every task of a generated roadmap into a week and tidies milestones.

The AI is asked for weeks, but it cannot be trusted to give consistent ones,
so its answer is only used when it fits: inside the phase's span of weeks and
never earlier than the task before it. Otherwise the phase's weeks are shared
out in proportion to each task's estimated hours.
"""

MAX_MILESTONES = 4
MAX_MILESTONE_CHARS = 160


def _whole(value) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None

    return number if number >= 1 else None


def assign_weeks(phases: list[dict], first_week: int = 1) -> int:
    """Sets `week` on every task and returns the first week after the plan."""
    start = first_week

    for phase in phases:
        span = max(1, _whole(phase.get("estimated_weeks")) or 1)
        end = start + span - 1
        tasks = phase.get("tasks") or []
        hours = [max(1, _whole(t.get("estimated_hours")) or 1) for t in tasks]
        total = sum(hours) or 1
        done = 0
        previous = start

        for task, task_hours in zip(tasks, hours):
            proposed = _whole(task.get("week"))

            if proposed is None or not (start <= proposed <= end):
                proposed = start + (done * span) // total

            week = min(end, max(previous, proposed))
            task["week"] = week
            previous = week
            done += task_hours

        phase["start_week"] = start
        start = end + 1

    return start


def clean_milestones(raw) -> list[str]:
    if not isinstance(raw, list):
        return []

    cleaned: list[str] = []

    for item in raw:
        text = " ".join(str(item or "").split())[:MAX_MILESTONE_CHARS]

        if text and text not in cleaned:
            cleaned.append(text)

    return cleaned[:MAX_MILESTONES]


def normalize(roadmap_data: dict, first_week: int = 1) -> dict:
    """Weeks and milestones for a whole generated roadmap (changed in place)."""
    phases = roadmap_data.get("phases") or []

    for phase in phases:
        phase["milestones"] = clean_milestones(phase.get("milestones"))

    assign_weeks(phases, first_week)

    return roadmap_data
