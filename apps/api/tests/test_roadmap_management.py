"""Managing roadmaps: pause, resume, activate, delete, restore, task completion and the list."""
import asyncio
import selectors
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.enums import RoadmapStatus
from app.schemas.roadmap import AdaptRequest
from app.services import roadmap_service
from app.services.roadmap_service import RoadmapService

S = RoadmapStatus


def run(coro):
    return asyncio.run(coro, loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))


class Db:
    def __init__(self):
        self.commits = self.rollbacks = self.flushes = 0
        self.expired = False

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1

    async def flush(self):
        self.flushes += 1

    async def refresh(self, obj):
        pass

    def expire_all(self):
        self.expired = True


class Profiles:
    def __init__(self, profile):
        self.profile = profile

    async def get_by_auth_user_id(self, _):
        return self.profile


class Content:
    def __init__(self, roadmap=None, version=None):
        self.roadmap, self.version = roadmap, version
        self.saved, self.replaced = [], None

    async def load(self, roadmap_id):
        return self.roadmap

    async def get_version(self, roadmap_id, version_id):
        return self.version

    async def save_version(self, roadmap, reason):
        self.saved.append(reason)

    async def replace_all(self, roadmap, snapshot):
        self.replaced = snapshot


class Roadmaps:
    def __init__(self, found=None, listing=(), fail_delete=False):
        self.found, self.listing, self.fail_delete = found, list(listing), fail_delete
        self.archived = self.deleted = self.locked = self.status_set = None

    async def lock_profile(self, profile_id):
        self.locked = profile_id

    async def archive_active_roadmaps(self, profile_id, except_id=None):
        self.archived = (profile_id, except_id)

    async def get_by_id_for_profile(self, roadmap_id, profile_id):
        return self.found

    async def delete_roadmap(self, roadmap):
        if self.fail_delete:
            raise RuntimeError("nope")

        self.deleted = roadmap

    async def get_all_by_user(self, profile_id):
        return self.listing

    async def update_status(self, roadmap_id, status):
        self.status_set = (roadmap_id, status)

    async def get_by_id(self, roadmap_id, user_id=None):
        return SimpleNamespace(id=roadmap_id, restored=True)


class Tasks:
    def __init__(self, task=None, progress=None, by_roadmap=None):
        self.task, self.progress, self.by_roadmap = task, progress or {"total": 0, "completed": 0}, by_roadmap or {}

    async def get_task_for_user(self, task_id, profile_id):
        return self.task

    async def get_roadmap_progress(self, roadmap_id):
        return self.progress

    async def get_progress_for_roadmaps(self, ids):
        return self.by_roadmap


def roadmap(status=S.ACTIVE, **over):
    values = dict(
        id=uuid4(), profile_id=None, title="Plan", description="d", status=status, status_before_job=None,
        generation_error=None, updated_at=datetime.now(timezone.utc), phases=[], daily_hours=1, target_duration=3,
    )
    values.update(over)
    return SimpleNamespace(**values)


def make(rm=None, profile=True, **parts):
    me = SimpleNamespace(id=uuid4()) if profile else None
    service = RoadmapService.__new__(RoadmapService)
    service.db = Db()
    service.profile_repository = Profiles(me)
    service.content = parts.get("content") or Content(rm)
    service.roadmap_repository = parts.get("roadmaps") or Roadmaps(rm)
    service.roadmap_task_repository = parts.get("tasks") or Tasks()

    if rm is not None and me is not None:
        rm.profile_id = me.id

    return service


def refused(call, status):
    with pytest.raises(HTTPException) as caught:
        run(call)

    assert caught.value.status_code == status


# ---- who may touch a roadmap ---------------------------------------------------------------------------------------------------


def test_every_roadmap_action_needs_a_profile_and_ownership():
    nobody = make(roadmap(), profile=False)

    for call in (
        nobody.pause(uuid4(), uuid4()), nobody.resume(uuid4(), uuid4()), nobody.list_versions(uuid4(), uuid4()),
        nobody.activate_roadmap(uuid4(), uuid4()), nobody.delete_roadmap(uuid4(), uuid4()), nobody.get_all(uuid4()),
        nobody.start_regenerate(uuid4(), uuid4()),
    ):
        refused(call, 404)

    stranger = make(roadmap())
    stranger.content.roadmap.profile_id = uuid4()  # belongs to someone else

    for call in (stranger.pause(uuid4(), uuid4()), stranger.start_regenerate(uuid4(), uuid4()), stranger.get_status(uuid4(), uuid4())):
        refused(call, 404)


# ---- pause and resume ----------------------------------------------------------------------------------------------------------


def test_an_active_roadmap_can_be_paused_and_pausing_twice_is_harmless():
    rm = roadmap(S.ACTIVE)
    service = make(rm)
    run(service.pause(rm.id, uuid4()))

    assert rm.status == S.PAUSED and service.db.commits == 1

    run(service.pause(rm.id, uuid4()))

    assert service.db.commits == 1


@pytest.mark.parametrize("status", [S.COMPLETED, S.ARCHIVED, S.FAILED, S.GENERATING])
def test_only_an_active_roadmap_can_be_paused(status):
    refused(make(roadmap(status)).pause(uuid4(), uuid4()), 409)


def test_resuming_makes_it_the_only_active_one():
    rm = roadmap(S.PAUSED)
    service = make(rm)
    run(service.resume(rm.id, uuid4()))

    assert rm.status == S.ACTIVE
    assert service.roadmap_repository.archived[1] == rm.id  # the others are archived, this one is kept


def test_resuming_an_active_roadmap_changes_nothing_and_other_states_cannot_resume():
    active = roadmap(S.ACTIVE)
    service = make(active)
    run(service.resume(active.id, uuid4()))

    assert service.db.commits == 0
    refused(make(roadmap(S.ARCHIVED)).resume(uuid4(), uuid4()), 409)


# ---- activating ----------------------------------------------------------------------------------------------------------------


def test_activating_an_archived_roadmap_archives_the_current_one():
    rm = roadmap(S.ARCHIVED)
    service = make(rm)
    result = run(service.activate_roadmap(rm.id, uuid4()))

    assert rm.status == S.ACTIVE and result.message == "Roadmap activated successfully"
    assert service.roadmap_repository.archived is not None and service.db.commits == 1


def test_activating_the_active_roadmap_is_a_no_op():
    rm = roadmap(S.ACTIVE)
    service = make(rm)
    result = run(service.activate_roadmap(rm.id, uuid4()))

    assert result.message == "Roadmap is already active" and service.roadmap_repository.archived is None


@pytest.mark.parametrize("status", [S.PAUSED, S.COMPLETED, S.GENERATING, S.FAILED])
def test_other_roadmaps_cannot_be_activated_and_the_attempt_is_rolled_back(status):
    service = make(roadmap(status))
    refused(service.activate_roadmap(uuid4(), uuid4()), 409)

    assert service.db.rollbacks == 1


def test_activating_someone_elses_roadmap_is_a_404():
    refused(make(None).activate_roadmap(uuid4(), uuid4()), 404)


# ---- deleting ------------------------------------------------------------------------------------------------------------------


def test_deleting_removes_the_roadmap_and_commits():
    rm = roadmap()
    service = make(rm)
    run(service.delete_roadmap(rm.id, uuid4()))

    assert service.roadmap_repository.deleted is rm and service.db.commits == 1
    assert service.roadmap_repository.locked is not None  # serialised with other roadmap changes


def test_deleting_what_is_not_yours_or_failing_to_delete_rolls_back():
    service = make(None)
    refused(service.delete_roadmap(uuid4(), uuid4()), 404)
    assert service.db.rollbacks == 1

    rm = roadmap()
    failing = make(rm, roadmaps=Roadmaps(found=rm, fail_delete=True))

    with pytest.raises(RuntimeError):
        run(failing.delete_roadmap(rm.id, uuid4()))

    assert failing.db.rollbacks == 1 and failing.db.commits == 0


# ---- versions ------------------------------------------------------------------------------------------------------------------


def test_restoring_saves_the_current_plan_first_so_it_can_be_undone():
    rm = roadmap(title="Now")
    snapshot = {"title": "Before", "description": "older", "daily_hours": 2, "target_duration": 5}
    service = make(rm, content=Content(rm, version=SimpleNamespace(snapshot=snapshot)))
    restored = run(service.restore_version(rm.id, uuid4(), uuid4()))

    assert service.content.saved == ["restore"] and service.content.replaced == snapshot
    assert (rm.title, rm.description, rm.daily_hours, rm.target_duration) == ("Before", "older", 2, 5)
    assert service.db.expired and restored.restored is True


def test_a_snapshot_missing_fields_keeps_the_current_ones():
    rm = roadmap(title="Keep me", daily_hours=3)
    service = make(rm, content=Content(rm, version=SimpleNamespace(snapshot={})))
    run(service.restore_version(rm.id, uuid4(), uuid4()))

    assert rm.title == "Keep me" and rm.daily_hours == 3


def test_restoring_waits_for_a_running_update_and_needs_a_real_version():
    refused(make(roadmap(S.GENERATING)).restore_version(uuid4(), uuid4(), uuid4()), 409)

    rm = roadmap()
    refused(make(rm, content=Content(rm, version=None)).restore_version(rm.id, uuid4(), uuid4()), 404)


# ---- adapting and regenerating ---------------------------------------------------------------------------------------------------


def phase_with(*done):
    return SimpleNamespace(tasks=[SimpleNamespace(completed=d) for d in done])


def test_a_finished_roadmap_has_nothing_to_adapt():
    rm = roadmap(phases=[phase_with(True, True)])

    refused(make(rm).start_adapt(rm.id, uuid4(), AdaptRequest(reason="behind")), 409)


def test_regenerating_saves_a_version_and_marks_the_roadmap_busy():
    rm = roadmap(S.ACTIVE)
    service = make(rm)
    run(service.start_regenerate(rm.id, uuid4()))

    assert service.content.saved == ["regenerate"]
    assert rm.status == S.GENERATING and rm.status_before_job == "active"


def test_a_second_update_while_one_is_running_is_refused():
    running = roadmap(S.GENERATING, status_before_job="active")
    refused(make(running).start_regenerate(running.id, uuid4()), 409)


def test_an_update_that_never_reported_back_is_given_up_on_and_a_new_one_may_start():
    lost = roadmap(S.GENERATING, status_before_job="active", updated_at=datetime.now(timezone.utc) - timedelta(hours=2))
    service = make(lost)
    run(service.start_regenerate(lost.id, uuid4()))

    assert lost.status == S.GENERATING and lost.status_before_job == "active"  # started again from the restored state


def test_the_status_check_settles_a_lost_job():
    lost = roadmap(S.GENERATING, status_before_job=None, updated_at=datetime.now(timezone.utc) - timedelta(hours=2))
    service = make(lost)
    result = run(service.get_status(lost.id, uuid4()))

    assert result["status"] == S.FAILED and result["error"] and service.db.commits == 1


def test_a_healthy_status_check_does_not_write():
    rm = roadmap(S.ACTIVE)
    service = make(rm)

    assert run(service.get_status(rm.id, uuid4()))["status"] == S.ACTIVE and service.db.commits == 0


# ---- ticking tasks off -----------------------------------------------------------------------------------------------------------


def task(done=False):
    return SimpleNamespace(id=uuid4(), completed=done, phase=SimpleNamespace(roadmap_id=uuid4()))


@pytest.fixture
def evaluated(monkeypatch):
    seen = []

    class Achievements:
        def __init__(self, db):
            pass

        async def safe_evaluate(self, profile):
            seen.append(profile)

    monkeypatch.setattr(roadmap_service, "AchievementService", Achievements)
    return seen


def test_completing_a_task_awards_xp_and_keeps_the_roadmap_active(awards, evaluated):
    t = task()
    service = make(tasks=Tasks(t, {"total": 4, "completed": 1}))
    run(service.update_task_completion(t.id, True, uuid4()))

    assert t.completed is True and len(awards) == 1
    assert service.roadmap_repository.status_set == (t.phase.roadmap_id, S.ACTIVE)
    assert evaluated == [] and service.db.commits == 1


def test_completing_the_last_task_completes_the_roadmap_and_checks_achievements(awards, evaluated):
    t = task()
    service = make(tasks=Tasks(t, {"total": 4, "completed": 4}))
    run(service.update_task_completion(t.id, True, uuid4()))

    assert service.roadmap_repository.status_set[1] == S.COMPLETED and len(evaluated) == 1


def test_un_ticking_a_task_gives_no_xp_and_reopens_a_finished_roadmap(awards, evaluated):
    t = task(done=True)
    service = make(tasks=Tasks(t, {"total": 4, "completed": 3}))
    run(service.update_task_completion(t.id, False, uuid4()))

    assert t.completed is False and awards == []
    assert service.roadmap_repository.status_set[1] == S.ACTIVE


def test_a_roadmap_with_no_tasks_keeps_its_status(awards, evaluated):
    t = task()
    service = make(tasks=Tasks(t, {"total": 0, "completed": 0}))
    run(service.update_task_completion(t.id, True, uuid4()))

    assert service.roadmap_repository.status_set is None


def test_a_task_that_is_not_yours_cannot_be_ticked(awards):
    refused(make(tasks=Tasks(None)).update_task_completion(uuid4(), True, uuid4()), 404)
    assert awards == []


# ---- the list --------------------------------------------------------------------------------------------------------------------


def test_the_list_shows_progress_as_whole_percentages():
    a, b, c = roadmap(title="A"), roadmap(title="B"), roadmap(title="C")
    progress = {a.id: {"total": 3, "completed": 1}, b.id: {"total": 4, "completed": 4}}
    service = make(roadmaps=Roadmaps(listing=[a, b, c]), tasks=Tasks(by_roadmap=progress))
    rows = run(service.get_all(uuid4()))

    assert [(r["title"], r["progress"], r["total_tasks"]) for r in rows] == [("A", 33, 3), ("B", 100, 4), ("C", 0, 0)]
