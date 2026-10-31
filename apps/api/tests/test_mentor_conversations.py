"""The AI mentor's conversations: creating, listing, opening, sending, deleting."""
import asyncio
import selectors
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.mentor import MentorConversationCreateRequest, MentorMessageCreateRequest
from app.services import mentor_service
from app.services.mentor_context import MentorContext
from app.services.mentor_service import MentorService

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


def conversation(title="Chat"):
    return SimpleNamespace(id=uuid4(), title=title, created_at=NOW, updated_at=NOW)


def message(role, content):
    return SimpleNamespace(id=uuid4(), role=role, content=content, created_at=NOW)


class Mentor:
    def __init__(self, owned=None, history=(), total=0, fail_on=None):
        self.owned = owned
        self.history = list(history)
        self.total = total
        self.fail_on = fail_on
        self.created_title = None
        self.messages = []
        self.deleted = None
        self.touched = False
        self.page = None

    def _maybe_fail(self, what):
        if self.fail_on == what:
            raise RuntimeError(f"{what} failed")

    async def create_conversation(self, profile_id, title):
        self._maybe_fail("create_conversation")
        self.created_title = title
        return conversation(title)

    async def list_conversations(self, profile_id, limit, offset):
        self.page = (limit, offset)
        return [conversation(f"c{i}") for i in range(min(limit, max(self.total - offset, 0)))]

    async def count_conversations(self, profile_id):
        return self.total

    async def get_conversation_by_id(self, conversation_id, profile_id):
        return self.owned

    async def get_conversation_messages(self, conversation_id):
        return self.history

    async def get_recent_messages(self, conversation_id, limit):
        self.limit = limit
        return self.history

    async def create_message(self, conversation_id, role, content, prompt_version=None):
        self._maybe_fail("create_message")
        made = message(role, content)
        self.messages.append(made)
        return made

    async def touch_conversation(self, conv):
        self.touched = True

    async def delete_conversation(self, conv):
        self._maybe_fail("delete_conversation")
        self.deleted = conv


class Profiles:
    def __init__(self, profile):
        self.profile = profile

    async def get_by_auth_user_id(self, _):
        return self.profile


class Settings:
    def __init__(self, row=None):
        self.row = row

    async def get_by_profile_id(self, _):
        return self.row


class AI:
    def __init__(self, reply="Here is how closures work."):
        self.reply, self.calls = reply, []

    async def generate_response(self, messages, system_prompt=None, profile_id=None):
        self.calls.append({"messages": messages, "system": system_prompt, "profile": profile_id})
        return self.reply


@pytest.fixture(autouse=True)
def quiet_extras(monkeypatch):
    """Achievements and analytics are tested elsewhere."""
    evaluated = []

    class Achievements:
        def __init__(self, db):
            pass

        async def safe_evaluate(self, profile):
            evaluated.append(profile)

    async def no_context(db, profile):
        return MentorContext()

    monkeypatch.setattr(mentor_service, "AchievementService", Achievements)
    monkeypatch.setattr(mentor_service, "build_context", no_context)
    monkeypatch.setattr(mentor_service, "track", lambda *a, **k: None)
    return evaluated


def make(mentor=None, profile=True, settings=None, ai=None, language="en"):
    service = MentorService.__new__(MentorService)
    service.db = Db()
    service.profile_repository = Profiles(SimpleNamespace(id=uuid4(), language=language) if profile else None)
    service.mentor_repository = mentor or Mentor()
    service.settings_repository = Settings(settings)
    service.mentor_ai_service = ai or AI()
    return service


def expect_404(call):
    with pytest.raises(HTTPException) as caught:
        run(call)

    assert caught.value.status_code == 404


# ---- creating -----------------------------------------------------------------------------------------------------------------


def test_a_new_conversation_gets_its_title_trimmed():
    service = make()
    result = run(service.create_conversation(MentorConversationCreateRequest(title="  Python help  "), uuid4()))

    assert service.mentor_repository.created_title == "Python help" and result.title == "Python help"
    assert service.db.commits == 1


def test_a_conversation_that_cannot_be_saved_is_rolled_back():
    service = make(Mentor(fail_on="create_conversation"))

    with pytest.raises(RuntimeError):
        run(service.create_conversation(MentorConversationCreateRequest(), uuid4()))

    assert service.db.rollbacks == 1 and service.db.commits == 0


def test_every_conversation_call_needs_a_profile():
    service = make(profile=False)

    expect_404(service.create_conversation(MentorConversationCreateRequest(), uuid4()))
    expect_404(service.list_conversations(uuid4()))
    expect_404(service.get_conversation_detail(uuid4(), uuid4()))
    expect_404(service.send_message(uuid4(), MentorMessageCreateRequest(content="hi"), uuid4()))
    expect_404(service.delete_conversation(uuid4(), uuid4()))
    expect_404(service.suggestions(uuid4()))


# ---- listing ------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "total,page,size,pages,has_next,shown",
    [(0, 1, 10, 0, False, 0), (10, 1, 10, 1, False, 10), (25, 1, 10, 3, True, 10), (25, 3, 10, 3, False, 5)],
)
def test_the_list_pages_correctly(total, page, size, pages, has_next, shown):
    service = make(Mentor(total=total))
    result = run(service.list_conversations(uuid4(), page=page, page_size=size))

    assert (result.total, result.total_pages, result.has_next, len(result.conversations)) == (total, pages, has_next, shown)
    assert service.mentor_repository.page == (size, (page - 1) * size)


# ---- opening ------------------------------------------------------------------------------------------------------------------


def test_opening_a_conversation_shows_its_messages_in_order():
    owned = conversation("Closures")
    history = [message("user", "what is a closure?"), message("assistant", "A function that remembers.")]
    result = run(make(Mentor(owned=owned, history=history)).get_conversation_detail(owned.id, uuid4()))

    assert result.title == "Closures" and [m.role for m in result.messages] == ["user", "assistant"]


def test_someone_elses_conversation_cannot_be_opened_or_deleted():
    service = make(Mentor(owned=None))

    expect_404(service.get_conversation_detail(uuid4(), uuid4()))
    expect_404(service.delete_conversation(uuid4(), uuid4()))
    assert service.mentor_repository.deleted is None


# ---- sending ------------------------------------------------------------------------------------------------------------------


def test_the_reply_is_built_from_recent_history_then_the_new_question(quiet_extras):
    owned = conversation()
    ai = AI("A closure remembers its scope.")
    service = make(Mentor(owned=owned, history=[message("user", "hi"), message("assistant", "hello")]), ai=ai)
    result = run(service.send_message(owned.id, MentorMessageCreateRequest(content="  what is a closure?  "), uuid4()))

    assert [m["role"] for m in ai.calls[0]["messages"]] == ["user", "assistant", "user"]
    assert ai.calls[0]["messages"][-1]["content"] == "what is a closure?"
    assert service.mentor_repository.limit == 20
    assert result.assistant_message.content == "A closure remembers its scope."
    assert [m.role for m in service.mentor_repository.messages] == ["user", "assistant"]
    assert service.mentor_repository.touched and service.db.commits == 1
    assert len(quiet_extras) == 1  # achievements are checked after a message


def test_a_message_of_only_spaces_is_refused_before_the_ai_is_called():
    owned = conversation()
    ai = AI()
    service = make(Mentor(owned=owned), ai=ai)

    with pytest.raises(HTTPException) as caught:
        run(service.send_message(owned.id, MentorMessageCreateRequest(content="   "), uuid4()))

    assert caught.value.status_code == 422 and ai.calls == []


def test_a_conversation_that_is_not_yours_gets_no_reply():
    ai = AI()
    service = make(Mentor(owned=None), ai=ai)

    expect_404(service.send_message(uuid4(), MentorMessageCreateRequest(content="hi"), uuid4()))
    assert ai.calls == []


def test_the_tone_and_language_shape_the_system_prompt():
    owned = conversation()
    ai = AI()
    settings = SimpleNamespace(ai_mentor_enabled=True, ai_tone="genz")
    service = make(Mentor(owned=owned), settings=settings, ai=ai, language="ur-Latn")
    run(service.send_message(owned.id, MentorMessageCreateRequest(content="hi"), uuid4()))

    plain = AI()
    run(make(Mentor(owned=owned), ai=plain, language="en").send_message(owned.id, MentorMessageCreateRequest(content="hi"), uuid4()))

    assert ai.calls[0]["system"] != plain.calls[0]["system"]


def test_the_chat_still_works_when_the_learners_context_cannot_be_built(monkeypatch):
    async def broken(db, profile):
        raise RuntimeError("database hiccup")

    monkeypatch.setattr(mentor_service, "build_context", broken)
    owned = conversation()
    service = make(Mentor(owned=owned))
    result = run(service.send_message(owned.id, MentorMessageCreateRequest(content="hi"), uuid4()))

    assert result.assistant_message.role == "assistant"
    assert service.db.rollbacks == 1  # the failed lookup is cleaned up before carrying on


def test_a_failure_while_saving_the_reply_is_rolled_back():
    owned = conversation()
    service = make(Mentor(owned=owned, fail_on="create_message"))

    with pytest.raises(RuntimeError):
        run(service.send_message(owned.id, MentorMessageCreateRequest(content="hi"), uuid4()))

    assert service.db.rollbacks == 1 and service.db.commits == 0


# ---- suggestions and deleting ---------------------------------------------------------------------------------------------------


def test_suggestions_come_from_the_learners_context(monkeypatch):
    async def with_chips(db, profile):
        return MentorContext(chips=["Explain HTTP", "Review my code"])

    monkeypatch.setattr(mentor_service, "build_context", with_chips)

    assert run(make().suggestions(uuid4())) == ["Explain HTTP", "Review my code"]


def test_deleting_removes_the_conversation_and_commits():
    owned = conversation()
    service = make(Mentor(owned=owned))
    run(service.delete_conversation(owned.id, uuid4()))

    assert service.mentor_repository.deleted is owned and service.db.commits == 1


def test_a_failed_delete_is_rolled_back():
    owned = conversation()
    service = make(Mentor(owned=owned, fail_on="delete_conversation"))

    with pytest.raises(RuntimeError):
        run(service.delete_conversation(owned.id, uuid4()))

    assert service.db.rollbacks == 1 and service.db.commits == 0
