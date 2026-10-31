"""Finishing a lesson: XP once, never while it is still being written, never for someone else's lesson."""
import asyncio
import selectors
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services import task_learning_unit_service as module
from app.services.gamification_service import GamificationService
from app.services.task_learning_unit_service import TaskLearningUnitService, career_is_coding


def run(coro):
    return asyncio.run(coro, loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))


class Db:
    def __init__(self):
        self.commits = self.rollbacks = 0

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1

    async def refresh(self, obj):
        pass


class Profiles:
    def __init__(self, profile):
        self.profile = profile

    async def get_by_auth_user_id(self, _):
        return self.profile


class Units:
    def __init__(self, unit, fail=False):
        self.unit, self.fail, self.for_update = unit, fail, None

    async def get_by_id_for_user(self, unit_id, profile_id, for_update=False):
        self.for_update = for_update
        return self.unit

    async def update_completion(self, unit, completed):
        if self.fail:
            raise RuntimeError("write failed")

        unit.completed = completed
        return unit


class Activities:
    def __init__(self):
        self.recorded = []

    async def create_completion_activity(self, profile_id, learning_unit_id, estimated_minutes):
        self.recorded.append((learning_unit_id, estimated_minutes))


def make(unit, profile=True, fail=False):
    service = TaskLearningUnitService.__new__(TaskLearningUnitService)
    service.db = Db()
    service.profile_repository = Profiles(SimpleNamespace(id=uuid4()) if profile else None)
    service.learning_unit_repository = Units(unit, fail)
    service.learning_activity_repository = Activities()
    service.gamification = GamificationService(service.db)
    return service


def lesson(done=False, status="ready", minutes=25):
    return SimpleNamespace(id=uuid4(), completed=done, status=status, estimated_minutes=minutes)


def test_the_first_completion_records_the_study_time_and_awards_xp(awards):
    unit = lesson()
    service = make(unit)
    result = run(service.update_completion(unit.id, True, uuid4()))

    assert result.completed is True
    assert service.learning_activity_repository.recorded == [(unit.id, 25)]
    assert [(reason, ref) for reason, _, ref in awards] == [(module.REASON_LESSON, unit.id)]
    assert service.db.commits == 1
    assert service.learning_unit_repository.for_update is True  # two taps at once cannot both count


def test_completing_a_lesson_again_gives_no_second_award(awards):
    unit = lesson(done=True)
    service = make(unit)
    run(service.update_completion(unit.id, True, uuid4()))

    assert awards == [] and service.learning_activity_repository.recorded == []


def test_marking_a_lesson_not_done_awards_nothing(awards):
    unit = lesson(done=True)
    result = run(make(unit).update_completion(unit.id, False, uuid4()))

    assert result.completed is False and awards == []


def test_a_lesson_without_a_length_records_zero_minutes(awards):
    unit = lesson(minutes=None)
    service = make(unit)
    run(service.update_completion(unit.id, True, uuid4()))

    assert service.learning_activity_repository.recorded == [(unit.id, 0)]


@pytest.mark.parametrize("status", ["pending", "writing", "failed"])
def test_a_lesson_that_is_not_written_yet_cannot_be_completed(awards, status):
    unit = lesson(status=status)
    service = make(unit)

    with pytest.raises(HTTPException) as caught:
        run(service.update_completion(unit.id, True, uuid4()))

    assert caught.value.status_code == 409
    assert awards == [] and unit.completed is False and service.db.rollbacks == 1


def test_a_lesson_that_is_not_yours_is_a_404(awards):
    service = make(None)

    with pytest.raises(HTTPException) as caught:
        run(service.update_completion(uuid4(), True, uuid4()))

    assert caught.value.status_code == 404 and awards == []


def test_no_profile_is_a_404_before_anything_is_looked_up():
    service = make(lesson(), profile=False)

    with pytest.raises(HTTPException) as caught:
        run(service.update_completion(uuid4(), True, uuid4()))

    assert caught.value.status_code == 404 and service.learning_unit_repository.for_update is None


def test_a_failed_save_is_rolled_back_and_gives_no_award(awards):
    unit = lesson()
    service = make(unit, fail=True)

    with pytest.raises(RuntimeError):
        run(service.update_completion(unit.id, True, uuid4()))

    assert service.db.rollbacks == 1 and service.db.commits == 0 and awards == []


def test_reading_a_lesson_checks_it_belongs_to_the_learner():
    service = make(None)

    with pytest.raises(HTTPException) as caught:
        run(service.get_by_id(uuid4(), uuid4()))

    assert caught.value.status_code == 404

    unit = lesson()
    assert run(make(unit).get_by_id(unit.id, uuid4())) is unit


# ---- which careers get coding exercises --------------------------------------------------------------------------------------


class Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


def career_db(value=None, fail=False):
    class FakeDb:
        async def execute(self, statement):
            if fail:
                raise RuntimeError("no such table")

            return Result(value)

    return FakeDb()


def test_an_unknown_career_leaves_the_decision_to_the_catalogue_file():
    assert run(career_is_coding(career_db(None), "mystery")) is None


def test_a_database_problem_also_leaves_it_to_the_catalogue_file():
    assert run(career_is_coding(career_db(fail=True), "backend-engineer")) is None


def test_the_career_category_decides(monkeypatch):
    monkeypatch.setattr(module, "is_coding_category", lambda category: category == "software")

    assert run(career_is_coding(career_db("software"), "backend-engineer")) is True
    assert run(career_is_coding(career_db("design"), "ui-ux")) is False


# ---- re-queuing failed lessons and listing a task's lessons ---------------------------------------------------------------------


class Tasks:
    def __init__(self, task):
        self.task, self.asked = task, []

    async def get_task_for_user(self, task_id, profile_id, fresh=False):
        self.asked.append(fresh)
        return self.task


def test_retrying_puts_failed_lessons_back_and_returns_the_fresh_task(monkeypatch):
    requeued = []

    async def fake_requeue(db, task_id):
        requeued.append(task_id)
        return 2

    monkeypatch.setattr(module, "requeue_failed", fake_requeue)
    task = SimpleNamespace(id=uuid4())
    service = make(None)
    service.task_repository = Tasks(task)
    result = run(service.requeue_failed(task.id, uuid4()))

    assert result is task and requeued == [task.id]
    assert service.db.commits == 1 and service.task_repository.asked == [False, True]


def test_retrying_needs_a_profile_and_a_task_that_is_yours(monkeypatch):
    async def never(db, task_id):
        raise AssertionError("must not be called")

    monkeypatch.setattr(module, "requeue_failed", never)

    for service in (make(None, profile=False), make(None)):
        service.task_repository = Tasks(None)

        with pytest.raises(HTTPException) as caught:
            run(service.requeue_failed(uuid4(), uuid4()))

        assert caught.value.status_code == 404


def test_a_tasks_lessons_are_listed_only_for_its_owner():
    class ByTask:
        async def get_by_task_for_user(self, task_id, profile_id):
            return ["lesson-1", "lesson-2"]

    service = make(None)
    service.learning_unit_repository = ByTask()

    assert run(service.get_by_task(uuid4(), uuid4())) == ["lesson-1", "lesson-2"]

    with pytest.raises(HTTPException) as caught:
        run(make(None, profile=False).get_by_task(uuid4(), uuid4()))

    assert caught.value.status_code == 404


def test_reading_a_lesson_needs_a_profile():
    with pytest.raises(HTTPException) as caught:
        run(make(lesson(), profile=False).get_by_id(uuid4(), uuid4()))

    assert caught.value.status_code == 404


def test_the_service_can_be_built_on_a_session():
    service = TaskLearningUnitService(SimpleNamespace())

    assert service.generator is not None and service.gamification is not None
