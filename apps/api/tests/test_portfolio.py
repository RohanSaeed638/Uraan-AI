import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.ai.services.portfolio_generator import build_prompt
from app.schemas.portfolio import (
    ChecklistUpdateRequest,
    CreateProjectRequest,
    ProjectFields,
    UpdatePortfolioRequest,
)
from app.services.portfolio_service import (
    PortfolioService,
    checklist_items,
    slugify,
)


@pytest.mark.parametrize(
    "name,expected",
    [
        ("Rohan Saeed", "rohan"),
        ("  ", "learner"),
        (None, "learner"),
        ("Zoë-Ann Khan", "zo-ann"),
        ("محمد علی", "learner"),
    ],
)
def test_slugify(name, expected):
    assert slugify(name) == expected


@pytest.mark.parametrize(
    "url",
    ["javascript:alert(1)", "ftp://x.com", "github.com/me/x", "http://a b.com"],
)
def test_project_links_must_be_http(url):
    with pytest.raises(ValidationError):
        ProjectFields(repo_url=url)


def test_project_fields_clean_input():
    fields = ProjectFields(
        repo_url="  https://github.com/me/todo ",
        live_url="   ",
        tech=["Python", " FastAPI ", "Python", ""],
    )

    assert fields.repo_url == "https://github.com/me/todo"
    assert fields.live_url is None
    assert fields.tech == ["Python", "FastAPI"]


@pytest.mark.parametrize("slug", ["ab", "-bad-", "Has Space", "admin", "x" * 41])
def test_bad_slugs_rejected(slug):
    with pytest.raises(ValidationError):
        UpdatePortfolioRequest(slug=slug)


def test_good_slug_is_normalised():
    assert UpdatePortfolioRequest(slug=" My-Name-1 ").slug == "my-name-1"


def test_checklist_rejects_unknown_item():
    with pytest.raises(ValidationError):
        ChecklistUpdateRequest(item_id="nope", done=True)


def test_checklist_items_reflect_state():
    items = {i.id: i.done for i in checklist_items({"readme": True})}

    assert items["readme"] is True
    assert items["live"] is False
    assert checklist_items(None)


def test_draft_prompt_uses_only_given_facts():
    prompt = build_prompt("Todo API", ["Python", "FastAPI"], "Build an API", None)

    assert "Todo API" in prompt
    assert "Python, FastAPI" in prompt
    assert "Do not invent" in prompt
    assert "(none)" in prompt


class _Db:
    def __init__(self):
        self.commits = 0

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        pass

    async def refresh(self, obj):
        obj.id = getattr(obj, "id", None) or uuid4()


class _Repo:
    def __init__(self, unit=None, taken=()):
        self.unit = unit
        self.taken = set(taken)
        self.projects = []
        self.portfolio = SimpleNamespace(
            headline=None, bio=None, slug=None, is_public=False, checklist={}
        )

    async def get_or_create(self, profile_id):
        return self.portfolio

    async def slug_taken(self, slug, except_profile_id):
        return slug in self.taken

    async def count_projects(self, profile_id):
        return len(self.projects)

    async def list_projects(self, profile_id):
        return self.projects

    async def suggestions(self, profile_id, limit=20):
        return []

    async def owned_project_unit(self, unit_id, profile_id):
        return self.unit

    async def add_project(self, project):
        project.id = uuid4()
        project.tech = project.tech or []
        self.projects.append(project)
        return project


class _Profiles:
    async def get_by_auth_user_id(self, auth_user_id):
        return SimpleNamespace(id=uuid4(), full_name="Rohan Saeed")


def _service(repo):
    service = PortfolioService.__new__(PortfolioService)
    service.db = _Db()
    service.profile_repository = _Profiles()
    service.repository = repo
    return service


def _unit(completed):
    unit = SimpleNamespace(
        id=uuid4(), title="Build a todo API", description="Brief", completed=completed
    )
    return unit, SimpleNamespace(title="REST APIs")


def test_project_from_completed_lesson_defaults_from_lesson():
    unit_row = _unit(True)
    repo = _Repo(unit=unit_row)
    service = _service(repo)

    result = asyncio.run(
        service.create_project(
            CreateProjectRequest(source_unit_id=unit_row[0].id), uuid4()
        )
    )

    assert result.title == "Build a todo API"
    assert result.description == "Brief"
    assert result.visible is True
    assert service.db.commits == 1


def test_project_from_unfinished_lesson_is_refused():
    repo = _Repo(unit=_unit(False))
    service = _service(repo)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            service.create_project(
                CreateProjectRequest(source_unit_id=uuid4()), uuid4()
            )
        )

    assert exc.value.status_code == 422
    assert repo.projects == []


def test_project_from_someone_elses_lesson_is_404():
    service = _service(_Repo(unit=None))

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            service.create_project(
                CreateProjectRequest(source_unit_id=uuid4()), uuid4()
            )
        )

    assert exc.value.status_code == 404


def test_manual_project_needs_a_title():
    service = _service(_Repo())

    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.create_project(CreateProjectRequest(), uuid4()))

    assert exc.value.status_code == 422


def test_going_public_assigns_a_free_slug():
    repo = _Repo()
    service = _service(repo)

    result = asyncio.run(
        service.update(UpdatePortfolioRequest(is_public=True), uuid4())
    )

    assert result.is_public is True
    assert result.slug.startswith("rohan-")


def test_taken_slug_is_a_conflict():
    service = _service(_Repo(taken={"rohan"}))

    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.update(UpdatePortfolioRequest(slug="rohan"), uuid4()))

    assert exc.value.status_code == 409
