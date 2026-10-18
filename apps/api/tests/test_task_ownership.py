import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services.roadmap_task_service import RoadmapTaskService


class _Db:
    async def commit(self):
        pass

    async def refresh(self, obj):
        pass


class _Profiles:
    def __init__(self, profile):
        self.profile = profile

    async def get_by_auth_user_id(self, auth_user_id):
        return self.profile


class _Tasks:
    """Returns the task only for the profile that owns it."""

    def __init__(self, task, owner_id):
        self.task = task
        self.owner_id = owner_id

    async def get_task_for_user(self, task_id, profile_id):
        return self.task if profile_id == self.owner_id else None


def _service(profile, task, owner_id):
    service = RoadmapTaskService(_Db())
    service.profile_repository = _Profiles(profile)
    service.repository = _Tasks(task, owner_id)
    return service


def test_owner_can_complete_task():
    owner = SimpleNamespace(id=uuid4())
    task = SimpleNamespace(completed=False)
    service = _service(owner, task, owner.id)

    result = asyncio.run(service.update_completion(uuid4(), True, uuid4()))

    assert result.completed is True


def test_other_users_cannot_complete_task():
    owner_id = uuid4()
    intruder = SimpleNamespace(id=uuid4())
    task = SimpleNamespace(completed=False)
    service = _service(intruder, task, owner_id)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.update_completion(uuid4(), True, uuid4()))

    assert exc.value.status_code == 404
    assert task.completed is False


def test_missing_profile_is_404():
    service = _service(None, SimpleNamespace(completed=False), uuid4())

    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.get_task(uuid4(), uuid4()))

    assert exc.value.status_code == 404
