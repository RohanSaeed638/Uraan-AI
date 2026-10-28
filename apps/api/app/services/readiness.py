"""The career readiness score: how close a learner is to being job-ready, 0 to
100, with the reasons and what to do next.

    tasks done        35 points
    projects          20
    consistency       15
    mock interviews   15
    portfolio         15

`compute_readiness` is a pure function of a few numbers so the formula can be
tested exactly; `ReadinessService` (below) only gathers those numbers."""
from dataclasses import dataclass

WEIGHTS = {
    "tasks": 35,
    "projects": 20,
    "consistency": 15,
    "interviews": 15,
    "portfolio": 15,
}

# Days studied in the last 28 that count as fully consistent. Nobody studies
# every single day for a month, so 20 earns full marks.
TARGET_ACTIVE_DAYS = 20
WINDOW_DAYS = 28

# Interviews that earn the full "practice" half of the interview score.
TARGET_INTERVIEWS = 3
# Portfolio projects that earn the full "projects" part of the portfolio score.
TARGET_PORTFOLIO_PROJECTS = 3

LEVELS = [
    (75, "job_ready"),
    (50, "almost_there"),
    (25, "building"),
    (0, "getting_started"),
]


@dataclass
class ReadinessStats:
    tasks_done: int = 0
    tasks_total: int = 0
    projects_done: int = 0
    projects_total: int = 0
    active_days: int = 0
    interviews_done: int = 0
    interview_avg_score: float = 0.0  # 0 to 100, over the latest few
    portfolio_public: bool = False
    portfolio_projects: int = 0
    portfolio_intro: bool = False


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def component_values(stats: ReadinessStats) -> dict[str, float]:
    """Each part of the score as 0..1."""
    tasks = stats.tasks_done / stats.tasks_total if stats.tasks_total else 0.0
    projects = stats.projects_done / stats.projects_total if stats.projects_total else 0.0
    consistency = stats.active_days / TARGET_ACTIVE_DAYS

    if stats.interviews_done:
        interviews = 0.5 * _clamp(stats.interviews_done / TARGET_INTERVIEWS) + 0.5 * _clamp(
            stats.interview_avg_score / 100
        )
    else:
        interviews = 0.0

    portfolio = (
        0.4 * (1 if stats.portfolio_public else 0)
        + 0.4 * _clamp(stats.portfolio_projects / TARGET_PORTFOLIO_PROJECTS)
        + 0.2 * (1 if stats.portfolio_intro else 0)
    )

    return {
        "tasks": _clamp(tasks),
        "projects": _clamp(projects),
        "consistency": _clamp(consistency),
        "interviews": _clamp(interviews),
        "portfolio": _clamp(portfolio),
    }


def _tip(key: str, stats: ReadinessStats) -> dict:
    """What would improve this part, with the page to do it on."""
    if key == "tasks":
        left = max(stats.tasks_total - stats.tasks_done, 0)

        return {
            "key": key,
            "action": "finish_tasks" if stats.tasks_total else "start_roadmap",
            "count": left,
            "href": "/learning" if stats.tasks_total else "/roadmaps",
        }

    if key == "projects":
        return {
            "key": key,
            "action": "finish_projects" if stats.projects_total else "add_projects",
            "count": max(stats.projects_total - stats.projects_done, 0),
            "href": "/projects",
        }

    if key == "consistency":
        return {
            "key": key,
            "action": "study_more_days",
            "count": max(TARGET_ACTIVE_DAYS - stats.active_days, 0),
            "href": "/learning",
        }

    if key == "interviews":
        return {
            "key": key,
            "action": "practice_interview",
            "count": max(TARGET_INTERVIEWS - stats.interviews_done, 0),
            "href": "/interview",
        }

    if not stats.portfolio_public:
        action = "publish_portfolio"
    elif stats.portfolio_projects < TARGET_PORTFOLIO_PROJECTS:
        action = "add_portfolio_projects"
    else:
        action = "complete_portfolio_intro"

    return {
        "key": key,
        "action": action,
        "count": max(TARGET_PORTFOLIO_PROJECTS - stats.portfolio_projects, 0),
        "href": "/portfolio",
    }


def level_for_score(score: int) -> str:
    for minimum, name in LEVELS:
        if score >= minimum:
            return name

    return LEVELS[-1][1]


def compute_readiness(stats: ReadinessStats) -> dict:
    values = component_values(stats)

    components = [
        {
            "key": key,
            "weight": weight,
            "value": round(values[key], 3),
            "points": round(weight * values[key], 1),
        }
        for key, weight in WEIGHTS.items()
    ]

    score = round(sum(c["points"] for c in components))

    # The biggest gaps first: the points still on the table, not the percentage.
    gaps = sorted(
        (c for c in components if c["value"] < 1),
        key=lambda c: c["weight"] * (1 - c["value"]),
        reverse=True,
    )

    return {
        "score": score,
        "level": level_for_score(score),
        "components": components,
        "tips": [_tip(c["key"], stats) for c in gaps[:3]],
    }
