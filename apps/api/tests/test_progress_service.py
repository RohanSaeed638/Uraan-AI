"""The numbers on the Progress page: percentages, roadmap counts and hours."""
import asyncio
import selectors
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.repositories.roadmap_repository import RoadmapRepository
from app.services import progress_service
from app.services.progress_service import (
    calculate_completion,
    calculate_percentage,
    get_progress_overview,
    get_roadmap_progress,
)


def run(coro):
    return asyncio.run(coro, loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))


@pytest.mark.parametrize("done,total,expected", [(0, 0, 0.0), (0, 5, 0.0), (1, 3, 33.33), (2, 3, 66.67), (4, 4, 100.0)])
def test_percentages_are_rounded_and_safe_with_nothing_to_do(done, total, expected):
    assert calculate_percentage(done, total) == expected
    assert calculate_completion(done, total) == expected


def unit(done):
    return SimpleNamespace(completed=done)


def task(done, units=()):
    return SimpleNamespace(completed=done, learning_units=list(units))


def phase(order, title, tasks):
    return SimpleNamespace(id=uuid4(), order=order, title=title, tasks=tasks)


def test_a_roadmaps_progress_counts_tasks_and_lessons_and_orders_phases(monkeypatch):
    roadmap = SimpleNamespace(
        id=uuid4(),
        phases=[
            phase(2, "Second", [task(False, [unit(False)])]),
            phase(1, "First", [task(True, [unit(True), unit(True)]), task(False, [unit(False)])]),
        ],
    )

    async def fake(self, db, roadmap_id, user_id):
        return roadmap

    monkeypatch.setattr(RoadmapRepository, "get_roadmap_for_progress", fake)
    result = run(get_roadmap_progress(db=None, roadmap_id=roadmap.id, user_id=uuid4()))

    assert [p.title for p in result.phases] == ["First", "Second"]
    assert (result.total_phases, result.total_tasks, result.completed_tasks, result.remaining_tasks) == (2, 3, 1, 2)
    assert result.completion_percentage == 33.33
    assert (result.total_learning_units, result.completed_learning_units) == (4, 2)
    assert result.learning_completion_percentage == 50.0
    assert result.phases[0].completion_percentage == 50.0


def test_a_roadmap_with_no_tasks_is_zero_percent_not_a_crash(monkeypatch):
    roadmap = SimpleNamespace(id=uuid4(), phases=[phase(1, "Empty", [])])

    async def fake(self, db, roadmap_id, user_id):
        return roadmap

    monkeypatch.setattr(RoadmapRepository, "get_roadmap_for_progress", fake)
    result = run(get_roadmap_progress(None, roadmap.id, uuid4()))

    assert result.completion_percentage == 0.0 and result.learning_completion_percentage == 0.0


def test_someone_elses_or_missing_roadmap_is_a_404(monkeypatch):
    async def fake(self, db, roadmap_id, user_id):
        return None

    monkeypatch.setattr(RoadmapRepository, "get_roadmap_for_progress", fake)

    with pytest.raises(HTTPException) as caught:
        run(get_roadmap_progress(None, uuid4(), uuid4()))

    assert caught.value.status_code == 404


def test_the_overview_adds_up_roadmaps_tasks_lessons_and_hours(monkeypatch):
    done_id, active_id, paused_id = uuid4(), uuid4(), uuid4()
    rows = [
        SimpleNamespace(roadmap_id=done_id, title="Done", status="completed", total_tasks=4, completed_tasks=4),
        SimpleNamespace(roadmap_id=active_id, title="Active", status=SimpleNamespace(value="active"), total_tasks=6, completed_tasks=3),
        SimpleNamespace(roadmap_id=paused_id, title="Paused", status="paused", total_tasks=0, completed_tasks=0),
    ]
    phases = [
        SimpleNamespace(roadmap_id=active_id, phase_id=uuid4(), title="Basics", total_tasks=2, completed_tasks=1),
        SimpleNamespace(roadmap_id=active_id, phase_id=uuid4(), title="More", total_tasks=4, completed_tasks=2),
    ]

    async def roadmaps(db, user_id):
        return rows

    async def learning(db, user_id):
        return SimpleNamespace(total_units=20, completed_units=5, completed_minutes=150)

    async def phase_stats(db, user_id):
        return phases

    monkeypatch.setattr(progress_service, "get_user_roadmap_statistics", roadmaps)
    monkeypatch.setattr(progress_service, "get_user_learning_statistics", learning)
    monkeypatch.setattr(progress_service, "get_user_phase_statistics", phase_stats)

    result = run(get_progress_overview(None, uuid4()))

    assert (result.roadmaps.total, result.roadmaps.completed, result.roadmaps.in_progress) == (3, 1, 1)
    assert (result.tasks.total, result.tasks.completed, result.tasks.remaining) == (10, 7, 3)
    assert result.tasks.completion_percentage == 70.0
    assert (result.learning_units.total, result.learning_units.completed) == (20, 5)
    assert result.learning_units.completion_percentage == 25.0
    assert result.estimated_completed_learning_hours == 2.5

    by_title = {r.title: r for r in result.roadmap_progress}
    assert len(by_title["Active"].phases) == 2 and by_title["Done"].phases == []
    assert by_title["Paused"].completion_percentage == 0.0


def test_a_new_account_has_an_all_zero_overview(monkeypatch):
    async def none(db, user_id):
        return []

    async def learning(db, user_id):
        return SimpleNamespace(total_units=0, completed_units=0, completed_minutes=0)

    monkeypatch.setattr(progress_service, "get_user_roadmap_statistics", none)
    monkeypatch.setattr(progress_service, "get_user_learning_statistics", learning)
    monkeypatch.setattr(progress_service, "get_user_phase_statistics", none)

    result = run(get_progress_overview(None, uuid4()))

    assert result.roadmaps.total == 0 and result.tasks.total == 0 and result.estimated_completed_learning_hours == 0.0
    assert result.roadmap_progress == []
