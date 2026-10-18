import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from openai import OpenAIError

from app.schemas.mentor import MentorMessageCreateRequest
from app.services.mentor_service import MentorService


class _Db:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True

    async def refresh(self, obj):
        pass


class _Profiles:
    async def get_by_auth_user_id(self, auth_user_id):
        return SimpleNamespace(id=uuid4())


class _Mentor:
    def __init__(self):
        self.created = []
        self.conversation = SimpleNamespace(id=uuid4())

    async def get_conversation_by_id(self, conversation_id, profile_id):
        return self.conversation

    async def get_recent_messages(self, conversation_id, limit):
        return [SimpleNamespace(role="user", content="earlier question")]

    async def create_message(self, conversation_id, role, content):
        message = SimpleNamespace(
            id=uuid4(),
            role=role,
            content=content,
            created_at=datetime.now(timezone.utc),
        )
        self.created.append(message)
        return message

    async def touch_conversation(self, conversation):
        pass


class _AI:
    def __init__(self, reply=None, error=None):
        self.reply = reply
        self.error = error
        self.received = None

    async def generate_response(self, messages):
        self.received = messages
        if self.error:
            raise self.error
        return self.reply


def _service(ai):
    service = MentorService.__new__(MentorService)
    service.db = _Db()
    service.profile_repository = _Profiles()
    service.mentor_repository = _Mentor()
    service.mentor_ai_service = ai
    return service


def _send(service):
    return asyncio.run(
        service.send_message(
            conversation_id=uuid4(),
            payload=MentorMessageCreateRequest(content="  what is a closure?  "),
            auth_user_id=uuid4(),
        )
    )


def test_send_message_stores_both_messages_and_replies():
    ai = _AI(reply="A closure captures its scope.")
    service = _service(ai)

    result = _send(service)

    assert result.assistant_message.content == "A closure captures its scope."
    assert result.user_message.content == "what is a closure?"
    assert [m.role for m in service.mentor_repository.created] == [
        "user",
        "assistant",
    ]
    assert service.db.committed
    # History plus the new user message is sent to the model.
    assert ai.received[-1] == {"role": "user", "content": "what is a closure?"}
    assert len(ai.received) == 2


def test_ai_failure_returns_503_and_saves_nothing():
    service = _service(_AI(error=OpenAIError("boom")))

    with pytest.raises(HTTPException) as exc:
        _send(service)

    assert exc.value.status_code == 503
    assert service.mentor_repository.created == []
    assert not service.db.committed
