"""Reading and changing a learner's settings."""
import asyncio
import selectors
from datetime import time
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.settings import UpdateUserSettingsRequest
from app.services.settings_service import SettingsService


def run(coro):
    return asyncio.run(coro, loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))


def row(profile_id, **over):
    values = dict(
        id=uuid4(), profile_id=profile_id, theme="system", email_notifications=True, learning_reminders=True,
        reminder_time=time(9, 0), timezone="Asia/Karachi", ai_mentor_enabled=True, ai_tone="friendly",
        wording="classic", show_on_leaderboard=True,
    )
    values.update(over)
    return SimpleNamespace(**values)


class FakeDb:
    def __init__(self):
        self.commits = self.rollbacks = self.executed = 0
        self.fail_on_execute = False

    async def execute(self, statement):
        self.executed += 1

        if self.fail_on_execute:
            raise RuntimeError("database went away")

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


class SettingsRepo:
    def __init__(self, existing=None, appears_after_insert=True):
        self.existing = existing
        self.appears_after_insert = appears_after_insert
        self.created = self.updates = None

    async def get_by_profile_id(self, profile_id):
        return self.existing

    async def create_default(self, profile_id):
        self.created = profile_id
        self.existing = row(profile_id)
        return self.existing

    async def update(self, settings, updates):
        self.updates = updates

        for key, value in updates.items():
            setattr(settings, key, value)

        return settings


def make(profile=True, existing=None):
    me = SimpleNamespace(id=uuid4()) if profile else None
    service = SettingsService.__new__(SettingsService)
    service.db = FakeDb()
    service.profile_repository = Profiles(me)
    service.settings_repository = SettingsRepo(existing=row(me.id) if (existing is True and me) else existing)
    return service, me


def test_existing_settings_are_returned_as_they_are():
    service, me = make(existing=True)
    result = run(service.get_settings(uuid4()))

    assert result.profile_id == me.id and result.timezone == "Asia/Karachi"
    assert service.db.commits == 0


def test_no_profile_is_a_404_for_reading_and_changing():
    service, _ = make(profile=False)

    for call in (service.get_settings(uuid4()), service.update_settings(UpdateUserSettingsRequest(theme="dark"), uuid4())):
        with pytest.raises(HTTPException) as caught:
            run(call)

        assert caught.value.status_code == 404


def test_first_visit_creates_default_settings_then_reads_them():
    service, me = make(existing=None)

    async def inserted(*args, **kwargs):
        service.settings_repository.existing = row(me.id)

    original = service.db.execute

    async def execute(statement):
        await original(statement)
        await inserted()

    service.db.execute = execute
    result = run(service.get_settings(uuid4()))

    assert result.profile_id == me.id
    assert service.db.commits == 1


def test_settings_that_still_do_not_exist_after_creating_them_are_a_500():
    service, _ = make(existing=None)

    with pytest.raises(HTTPException) as caught:
        run(service.get_settings(uuid4()))

    assert caught.value.status_code == 500


def test_a_database_failure_while_creating_rolls_back_and_is_raised():
    service, _ = make(existing=None)
    service.db.fail_on_execute = True

    with pytest.raises(RuntimeError):
        run(service.get_settings(uuid4()))

    assert service.db.rollbacks == 1


def test_only_the_fields_sent_are_changed():
    service, _ = make(existing=True)
    result = run(service.update_settings(UpdateUserSettingsRequest(theme="dark", learning_reminders=False), uuid4()))

    assert service.settings_repository.updates == {"theme": "dark", "learning_reminders": False}
    assert result.theme == "dark" and result.learning_reminders is False and result.email_notifications is True
    assert service.db.commits == 1


def test_an_empty_update_changes_nothing_and_does_not_write():
    service, _ = make(existing=True)
    run(service.update_settings(UpdateUserSettingsRequest(), uuid4()))

    assert service.settings_repository.updates is None and service.db.commits == 0


def test_changing_settings_before_any_exist_creates_them_first():
    service, me = make(existing=None)
    run(service.update_settings(UpdateUserSettingsRequest(wording="gamified"), uuid4()))

    assert service.settings_repository.created == me.id
    assert service.settings_repository.existing.wording == "gamified"


def test_a_failed_update_is_rolled_back():
    service, _ = make(existing=True)
    service.db.fail_on_execute = True

    with pytest.raises(RuntimeError):
        run(service.update_settings(UpdateUserSettingsRequest(theme="dark"), uuid4()))

    assert service.db.rollbacks == 1 and service.db.commits == 0


@pytest.mark.parametrize("bad", [{"timezone": "Mars/Olympus"}, {"theme": "neon"}, {"ai_tone": "rude"}])
def test_invalid_values_are_refused_before_anything_is_saved(bad):
    with pytest.raises(ValueError):
        UpdateUserSettingsRequest(**bad)
