import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.ai.services.document_generator import build_prompt
from app.schemas.document import GenerateDocumentRequest, UpdateDocumentRequest
from app.services.document_service import (
    MAX_DOCUMENTS,
    DocumentService,
    default_title,
)


def profile(**overrides):
    base = dict(
        id=uuid4(),
        full_name="Rohan Saeed",
        language="en",
        skill_level=SimpleNamespace(value="beginner"),
        learning_goal="Get a junior backend job",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_prompt_contains_only_supplied_facts():
    prompt = build_prompt(
        "resume",
        profile(),
        "Backend Developer",
        ["Learn HTTP", "Build a REST API"],
        ["Todo API"],
        "BS CS, Example University, 2025",
        None,
    )

    assert "Rohan Saeed" in prompt
    assert "- Learn HTTP" in prompt
    assert "- Todo API" in prompt
    assert "BS CS, Example University, 2025" in prompt
    assert "Never invent" in prompt


def test_prompt_marks_missing_data():
    prompt = build_prompt(
        "cover_letter", profile(), "Frontend Developer", [], [], None, None
    )

    assert "(none yet)" in prompt
    assert "cover letter" in prompt


def test_request_validation():
    assert GenerateDocumentRequest(kind="resume", target_role="  QA  ").target_role == "QA"

    with pytest.raises(ValidationError):
        GenerateDocumentRequest(kind="poem", target_role="QA")

    with pytest.raises(ValidationError):
        GenerateDocumentRequest(kind="resume", target_role="x")

    with pytest.raises(ValidationError):
        GenerateDocumentRequest(kind="resume", target_role="QA", surprise=1)

    with pytest.raises(ValidationError):
        UpdateDocumentRequest(content="")


def test_default_title():
    assert default_title("cover_letter", "Data Analyst") == (
        "Cover letter - Data Analyst"
    )


class _Db:
    def __init__(self):
        self.committed = False

    async def commit(self):
        self.committed = True

    async def rollback(self):
        pass

    async def refresh(self, obj):
        obj.id = uuid4()
        now = datetime.now(timezone.utc)
        obj.created_at = now
        obj.updated_at = now


class _Repo:
    def __init__(self, count=0):
        self._count = count
        self.created = []

    async def count(self, profile_id):
        return self._count

    async def completed_task_titles(self, profile_id):
        return ["Learn HTTP"]

    async def completed_project_titles(self, profile_id):
        return ["Todo API"]

    async def create(self, document):
        self.created.append(document)
        return document


class _Profiles:
    async def get_by_auth_user_id(self, auth_user_id):
        return profile()


class _Generator:
    def __init__(self, error=None):
        self.error = error
        self.kwargs = None

    async def generate(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return "# Rohan Saeed\n\n## Summary\nA beginner."


def _service(repo, generator):
    service = DocumentService.__new__(DocumentService)
    service.db = _Db()
    service.profile_repository = _Profiles()
    service.repository = repo
    service.generator = generator
    return service


def _generate(service):
    payload = GenerateDocumentRequest(kind="resume", target_role="Backend Developer")
    return asyncio.run(service.generate(payload, uuid4()))


def test_generate_stores_document_using_completed_work():
    repo, generator = _Repo(), _Generator()
    service = _service(repo, generator)

    result = _generate(service)

    assert result.kind == "resume"
    assert result.title == "Resume - Backend Developer"
    assert result.content.startswith("# Rohan Saeed")
    assert generator.kwargs["completed_tasks"] == ["Learn HTTP"]
    assert generator.kwargs["projects"] == ["Todo API"]
    assert service.db.committed
    assert len(repo.created) == 1


def test_generate_enforces_document_limit():
    service = _service(_Repo(count=MAX_DOCUMENTS), _Generator())

    with pytest.raises(HTTPException) as exc:
        _generate(service)

    assert exc.value.status_code == 409
    assert not service.db.committed


def test_ai_failure_returns_502_and_saves_nothing():
    repo = _Repo()
    service = _service(repo, _Generator(error=RuntimeError("boom")))

    with pytest.raises(HTTPException) as exc:
        _generate(service)

    assert exc.value.status_code == 502
    assert repo.created == []
    assert not service.db.committed
