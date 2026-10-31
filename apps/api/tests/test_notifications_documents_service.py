"""Notification settings and saved documents: reading, editing, deleting, and who may."""
import asyncio
import selectors
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.schemas.document import UpdateDocumentRequest
from app.schemas.notification import PushSubscribeRequest
from app.services.document_service import DocumentService
from app.services.notification_service import NotificationService

NOW = datetime(2026, 10, 31, tzinfo=timezone.utc)


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


def refused(call, status=404):
    with pytest.raises(HTTPException) as caught:
        run(call)

    assert caught.value.status_code == status


# ---- notifications -----------------------------------------------------------------------------------------------------------


class Notifications:
    def __init__(self, fail=False):
        self.fail, self.marked = fail, None

    async def mark_read(self, profile_id, notification_id):
        if self.fail:
            raise RuntimeError("nope")

        self.marked = (profile_id, notification_id)


class Subscriptions:
    def __init__(self, fail=False):
        self.fail, self.saved, self.removed = fail, None, None

    async def upsert(self, profile_id, endpoint, p256dh, auth):
        if self.fail:
            raise RuntimeError("nope")

        self.saved = (profile_id, endpoint, p256dh, auth)

    async def delete(self, profile_id, endpoint):
        if self.fail:
            raise RuntimeError("nope")

        self.removed = (profile_id, endpoint)


def notifier(profile=True, fail=False):
    service = NotificationService.__new__(NotificationService)
    service.db = Db()
    service.profile_repository = Profiles(SimpleNamespace(id=uuid4()) if profile else None)
    service.notifications = Notifications(fail)
    service.subscriptions = Subscriptions(fail)
    return service


SUBSCRIBE = PushSubscribeRequest(endpoint="https://push.example/abc", keys={"p256dh": "key", "auth": "secret"})


def test_one_or_all_notifications_are_marked_read():
    service = notifier()
    run(service.mark_read(uuid4(), None))

    assert service.notifications.marked[1] is None and service.db.commits == 1

    one = uuid4()
    run(service.mark_read(uuid4(), one))

    assert service.notifications.marked[1] == one


def test_a_device_is_registered_and_forgotten_for_the_right_learner():
    service = notifier()
    run(service.subscribe(uuid4(), SUBSCRIBE))
    profile_id = service.subscriptions.saved[0]

    assert service.subscriptions.saved[1:] == ("https://push.example/abc", "key", "secret")

    run(service.unsubscribe(uuid4(), "https://push.example/abc"))

    assert service.subscriptions.removed == (profile_id, "https://push.example/abc")
    assert service.db.commits == 2


def test_failed_writes_are_rolled_back():
    for action in (
        lambda s: s.mark_read(uuid4(), None),
        lambda s: s.subscribe(uuid4(), SUBSCRIBE),
        lambda s: s.unsubscribe(uuid4(), "x"),
    ):
        service = notifier(fail=True)

        with pytest.raises(RuntimeError):
            run(action(service))

        assert service.db.rollbacks == 1 and service.db.commits == 0


def test_nothing_works_without_a_profile():
    service = notifier(profile=False)

    refused(service.list(uuid4()))
    refused(service.mark_read(uuid4(), None))
    refused(service.subscribe(uuid4(), SUBSCRIBE))
    refused(service.unsubscribe(uuid4(), "x"))


def test_the_public_push_key_is_only_given_when_push_is_set_up(monkeypatch):
    service = notifier()
    monkeypatch.setattr(settings, "VAPID_PUBLIC_KEY", "")
    assert service.public_key() is None

    monkeypatch.setattr(settings, "VAPID_PUBLIC_KEY", "BPublicKey")
    assert service.public_key() == "BPublicKey"


# ---- documents ---------------------------------------------------------------------------------------------------------------


def stored(title="Resume - Backend", content="Experience..."):
    return SimpleNamespace(
        id=uuid4(), kind="resume", title=title, target_role="Backend", content=content, created_at=NOW, updated_at=NOW
    )


class Documents:
    def __init__(self, owned=None, rows=(), fail=False):
        self.owned, self.rows, self.fail, self.deleted = owned, list(rows), fail, None

    async def get_owned(self, document_id, profile_id):
        return self.owned

    async def list_for_profile(self, profile_id):
        return self.rows

    async def delete(self, document):
        if self.fail:
            raise RuntimeError("nope")

        self.deleted = document


def documents(owned=None, rows=(), profile=True, fail=False):
    service = DocumentService.__new__(DocumentService)
    service.db = Db()
    service.profile_repository = Profiles(SimpleNamespace(id=uuid4()) if profile else None)
    service.repository = Documents(owned, rows, fail)
    return service


def test_the_list_shows_every_document():
    result = run(documents(rows=[stored("A"), stored("B")]).list(uuid4()))

    assert [d.title for d in result.documents] == ["A", "B"]


def test_a_document_opens_for_its_owner_only():
    mine = stored()

    assert run(documents(owned=mine).get(mine.id, uuid4())).title == "Resume - Backend"
    refused(documents(owned=None).get(uuid4(), uuid4()))


def test_editing_changes_only_the_fields_sent():
    mine = stored()
    service = documents(owned=mine)
    result = run(service.update(mine.id, UpdateDocumentRequest(title="New title"), uuid4()))

    assert result.title == "New title" and result.content == "Experience..."
    assert service.db.commits == 1


def test_a_field_cannot_be_blanked_with_null():
    mine = stored()
    service = documents(owned=mine)
    refused(service.update(mine.id, UpdateDocumentRequest(content=None), uuid4()), status=422)

    assert mine.content == "Experience..."


def test_unknown_fields_and_empty_values_are_refused_before_anything_happens():
    with pytest.raises(ValueError):
        UpdateDocumentRequest(kind="cover_letter")

    with pytest.raises(ValueError):
        UpdateDocumentRequest(title="")


def test_someone_elses_document_cannot_be_edited_or_deleted():
    service = documents(owned=None)

    refused(service.update(uuid4(), UpdateDocumentRequest(title="x"), uuid4()))
    refused(service.delete(uuid4(), uuid4()))
    assert service.repository.deleted is None


def test_deleting_removes_the_document():
    mine = stored()
    service = documents(owned=mine)
    run(service.delete(mine.id, uuid4()))

    assert service.repository.deleted is mine and service.db.commits == 1


def test_a_failed_delete_is_rolled_back():
    mine = stored()
    service = documents(owned=mine, fail=True)

    with pytest.raises(RuntimeError):
        run(service.delete(mine.id, uuid4()))

    assert service.db.rollbacks == 1 and service.db.commits == 0


def test_no_profile_means_no_documents():
    service = documents(profile=False)

    refused(service.list(uuid4()))
    refused(service.get(uuid4(), uuid4()))
    refused(service.delete(uuid4(), uuid4()))
