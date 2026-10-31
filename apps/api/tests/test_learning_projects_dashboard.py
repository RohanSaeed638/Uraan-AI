"""What the learner is shown to continue: today's agenda, projects and the dashboard summary."""
import asyncio
import selectors
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.task_learning_unit import LearningUnitType
from app.repositories.roadmap_repository import RoadmapRepository
from app.services import dashboard_service, learning_service, project_service


def run(coro):
    return asyncio.run(coro, loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))


ROADMAP = SimpleNamespace(id=uuid4(), title="Backend")
PHASE = SimpleNamespace(id=uuid4(), title="Basics")


def task(title="Learn HTTP"):
    return SimpleNamespace(id=uuid4(), title=title)


def unit(title, day, order=1, done=False, minutes=20, kind="reading", **extra):
    values = dict(
        id=uuid4(), title=title, day=day, order=order, completed=done, estimated_minutes=minutes, type=kind,
        description=None, content="Do the thing", resource_url=None, details=None,
    )
    values.update(extra)
    return SimpleNamespace(**values)


# ---- continue learning ------------------------------------------------------------------------------------------------------


def test_continue_points_at_the_next_lesson(monkeypatch):
    t, u = task(), unit("Verbs", 2, kind=LearningUnitType.READING)

    async def nxt(db, user_id):
        return ROADMAP, PHASE, t, u

    monkeypatch.setattr(learning_service, "get_next_learning_unit", nxt)
    result = run(learning_service.get_continue_learning(None, uuid4()))

    assert (result.roadmap_id, result.task_id, result.learning_unit_id) == (ROADMAP.id, t.id, u.id)
    assert result.learning_unit_title == "Verbs" and result.day == 2


def test_continue_is_empty_when_everything_is_done(monkeypatch):
    async def nothing(db, user_id):
        return None

    monkeypatch.setattr(learning_service, "get_next_learning_unit", nothing)

    assert run(learning_service.get_continue_learning(None, uuid4())) is None


# ---- the learning agenda ------------------------------------------------------------------------------------------------------


def agenda_with(monkeypatch, rows, owned=True):
    async def fake_rows(db, user_id, roadmap_id):
        return rows

    async def fake_owned(db, user_id, roadmap_id):
        return ROADMAP if owned else None

    monkeypatch.setattr(learning_service, "get_roadmap_learning_units", fake_rows)
    monkeypatch.setattr(RoadmapRepository, "get_owned_roadmap", staticmethod(fake_owned))


def three_days():
    t = task()
    return [
        (ROADMAP, PHASE, t, unit("a", 1, 1, done=True, minutes=10)),
        (ROADMAP, PHASE, t, unit("b", 1, 2, done=True, minutes=15)),
        (ROADMAP, PHASE, t, unit("c", 2, 1, done=False, minutes=20)),
        (ROADMAP, PHASE, t, unit("d", 2, 2, done=False, minutes=30)),
        (ROADMAP, PHASE, t, unit("e", 3, 1, done=False, minutes=25)),
    ]


def test_today_shows_the_first_day_that_is_not_finished(monkeypatch):
    agenda_with(monkeypatch, three_days())
    result = run(learning_service.get_learning_agenda(None, uuid4(), ROADMAP.id, "today"))

    assert [u.title for d in result.days for u in d.units] == ["c", "d"]
    assert (result.total_units, result.completed_units, result.total_estimated_minutes) == (2, 0, 50)
    assert result.roadmap_title == "Backend" and result.view == "today"


def test_week_starts_there_and_includes_what_follows(monkeypatch):
    agenda_with(monkeypatch, three_days())
    result = run(learning_service.get_learning_agenda(None, uuid4(), ROADMAP.id, "week"))

    assert [len(d.units) for d in result.days] == [2, 1]


def test_all_shows_everything_including_finished_days(monkeypatch):
    agenda_with(monkeypatch, three_days())
    result = run(learning_service.get_learning_agenda(None, uuid4(), ROADMAP.id, "all"))

    assert result.total_units == 5 and result.completed_units == 2
    assert result.total_estimated_minutes == 100


def test_when_everything_is_done_today_is_empty(monkeypatch):
    t = task()
    agenda_with(monkeypatch, [(ROADMAP, PHASE, t, unit("a", 1, done=True))])
    result = run(learning_service.get_learning_agenda(None, uuid4(), ROADMAP.id, "today"))

    assert result.days == [] and result.total_units == 0


def test_the_same_day_of_two_tasks_is_two_separate_days(monkeypatch):
    first, second = task("one"), task("two")
    rows = [(ROADMAP, PHASE, first, unit("a", 1)), (ROADMAP, PHASE, second, unit("b", 1))]
    agenda_with(monkeypatch, rows)
    result = run(learning_service.get_learning_agenda(None, uuid4(), ROADMAP.id, "all"))

    assert len(result.days) == 2


def test_someone_elses_roadmap_has_no_agenda(monkeypatch):
    agenda_with(monkeypatch, [], owned=False)

    with pytest.raises(HTTPException) as caught:
        run(learning_service.get_learning_agenda(None, uuid4(), ROADMAP.id))

    assert caught.value.status_code == 404


# ---- projects ----------------------------------------------------------------------------------------------------------------


def test_project_details_are_read_from_the_lesson_and_tolerate_older_ones():
    rich = unit("p", 1, details={"difficulty": "beginner", "skills": ["git", "http"], "portfolio_value": "high"})
    old = unit("q", 1, details=None)

    assert project_service.project_meta(rich) == {
        "difficulty": "beginner", "skills": ["git", "http"], "portfolio_value": "high",
    }
    assert project_service.project_meta(old) == {"difficulty": None, "skills": [], "portfolio_value": None}


@pytest.mark.parametrize("status,expected", [("all", None), ("completed", True), ("pending", False)])
def test_the_status_filter_becomes_a_completed_filter(monkeypatch, status, expected):
    seen = {}

    async def rows(db, user_id, roadmap_id, completed):
        seen["completed"] = completed
        return []

    monkeypatch.setattr(project_service, "list_user_projects", rows)
    run(project_service.get_user_projects(None, uuid4(), status=status))

    assert seen["completed"] is expected


def test_the_project_list_counts_done_and_waiting(monkeypatch):
    t = task()
    rows = [
        (ROADMAP, PHASE, t, unit("done", 1, done=True, details={"skills": ["sql"]})),
        (ROADMAP, PHASE, t, unit("todo", 2, done=False)),
        (ROADMAP, PHASE, t, unit("todo2", 3, done=False)),
    ]

    async def listing(db, user_id, roadmap_id, completed):
        return rows

    monkeypatch.setattr(project_service, "list_user_projects", listing)
    result = run(project_service.get_user_projects(None, uuid4()))

    assert (result.total, result.completed, result.pending) == (3, 1, 2)
    assert result.projects[0].skills == ["sql"] and result.projects[0].roadmap_title == "Backend"


def test_a_project_opens_with_its_context(monkeypatch):
    t = task("Build an API")
    p = unit("Todo API", 4, content="Steps...", resource_url="https://example.com", details={"difficulty": "intermediate"})

    async def one(db, user_id, project_id):
        return ROADMAP, PHASE, t, p

    monkeypatch.setattr(project_service, "get_user_project_by_id", one)
    result = run(project_service.get_project_detail(None, uuid4(), p.id))

    assert result.instructions == "Steps..." and result.resource_url == "https://example.com"
    assert (result.roadmap.title, result.phase.title, result.task.title) == ("Backend", "Basics", "Build an API")
    assert result.difficulty == "intermediate"


def test_a_project_that_is_not_yours_is_a_404(monkeypatch):
    async def none(db, user_id, project_id):
        return None

    monkeypatch.setattr(project_service, "get_user_project_by_id", none)

    with pytest.raises(HTTPException) as caught:
        run(project_service.get_project_detail(None, uuid4(), uuid4()))

    assert caught.value.status_code == 404


# ---- dashboard ---------------------------------------------------------------------------------------------------------------


def patch_dashboard(monkeypatch, stats, progress=None, nxt=None):
    async def statistics(db, user_id):
        return stats

    async def roadmap_progress(db, roadmap_id, user_id):
        return progress

    async def continuing(db, user_id):
        return nxt

    monkeypatch.setattr(dashboard_service, "get_dashboard_statistics", statistics)
    monkeypatch.setattr(dashboard_service, "get_roadmap_progress", roadmap_progress)
    monkeypatch.setattr(dashboard_service, "get_continue_learning", continuing)


STATS = {"total_roadmaps": 2, "completed_roadmaps": 1, "total_tasks": 10, "completed_tasks": 4,
         "total_learning_units": 30, "completed_learning_units": 12}


def test_a_new_learner_gets_a_dashboard_with_no_roadmap_and_nothing_next(monkeypatch):
    patch_dashboard(monkeypatch, {k: 0 for k in STATS})
    result = run(dashboard_service.get_dashboard_summary(None, uuid4(), "Sana", None, current_roadmap=None))

    assert result.user.name == "Sana" and result.current_roadmap is None and result.next_learning is None
    assert result.stats.remaining_tasks == 0


def test_the_dashboard_combines_stats_the_current_roadmap_and_the_next_lesson(monkeypatch):
    progress = SimpleNamespace(total_phases=3, total_tasks=10, completed_tasks=4, completion_percentage=40.0)
    nxt = SimpleNamespace(
        roadmap_id=ROADMAP.id, task_id=uuid4(), learning_unit_id=uuid4(), task_title="Learn HTTP",
        learning_unit_title="Verbs", learning_unit_type="reading", estimated_minutes=20,
    )
    patch_dashboard(monkeypatch, dict(STATS), progress, nxt)
    result = run(dashboard_service.get_dashboard_summary(None, uuid4(), "Sana", "Backend", ROADMAP))

    assert result.current_roadmap.completion_percentage == 40.0 and result.current_roadmap.total_phases == 3
    assert result.next_learning.learning_unit_title == "Verbs"
    assert result.stats.remaining_tasks == 6 and result.stats.total_learning_units == 30
    assert result.user.career_goal == "Backend"
