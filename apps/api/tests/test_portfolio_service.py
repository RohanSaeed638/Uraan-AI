"""The public portfolio: publishing, projects, the checklist, AI descriptions and the public page."""
import asyncio
import selectors
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.schemas.portfolio import (
    ChecklistUpdateRequest,
    CreateProjectRequest,
    ProjectFields,
    UpdatePortfolioRequest,
)
from app.services import portfolio_service
from app.services.portfolio_service import MAX_PROJECTS, PortfolioService


def run(coro):
    return asyncio.run(coro, loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))


class Db:
    def __init__(self, commit_error=None):
        self.commits = self.rollbacks = 0
        self.commit_error = commit_error

    async def commit(self):
        if self.commit_error:
            raise self.commit_error

        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1

    async def refresh(self, obj):
        pass


def stored_project(title="API", visible=True, **over):
    values = dict(
        id=uuid4(), source_unit_id=None, title=title, description=None, repo_url=None, live_url=None,
        tech=["python"], visible=visible,
    )
    values.update(over)
    return SimpleNamespace(**values)


class Repo:
    def __init__(self, projects=(), taken=(), unit=None, public=None):
        self.projects = list(projects)
        self.taken = set(taken)
        self.unit, self.public_row = unit, public
        self.deleted = None
        self.portfolio = SimpleNamespace(headline=None, bio=None, slug=None, is_public=False, checklist={})

    async def get_or_create(self, profile_id):
        return self.portfolio

    async def slug_taken(self, slug, except_profile_id):
        return slug in self.taken

    async def count_projects(self, profile_id):
        return len(self.projects)

    async def list_projects(self, profile_id):
        return self.projects

    async def suggestions(self, profile_id, limit=20):
        return [(uuid4(), "Build an API", "REST APIs")]

    async def owned_project_unit(self, unit_id, profile_id):
        return self.unit

    async def add_project(self, project):
        project.id = uuid4()
        self.projects.append(project)

    async def get_project(self, project_id, profile_id):
        return next((p for p in self.projects if p.id == project_id), None)

    async def delete_project(self, project):
        self.deleted = project
        self.projects.remove(project)

    async def get_public(self, slug):
        self.asked_slug = slug
        return self.public_row


class Profiles:
    def __init__(self, profile):
        self.profile = profile

    async def get_by_auth_user_id(self, _):
        return self.profile


class Generator:
    def __init__(self, text="A short description.", error=None):
        self.text, self.error, self.seen = text, error, None

    async def draft_description(self, **kwargs):
        self.seen = kwargs

        if self.error:
            raise self.error

        return self.text


@pytest.fixture(autouse=True)
def quiet(monkeypatch):
    events, evaluated = [], []

    class Achievements:
        def __init__(self, db):
            pass

        async def safe_evaluate(self, profile):
            evaluated.append(profile)

    monkeypatch.setattr(portfolio_service, "AchievementService", Achievements)
    monkeypatch.setattr(portfolio_service, "track", lambda pid, name, **k: events.append(name))
    monkeypatch.setattr(portfolio_service, "use_profile", lambda *a, **k: None)
    return SimpleNamespace(events=events, evaluated=evaluated)


def make(repo=None, profile=True, db=None, generator=None, name="Rohan Saeed"):
    service = PortfolioService.__new__(PortfolioService)
    service.db = db or Db()
    service.profile_repository = Profiles(SimpleNamespace(id=uuid4(), full_name=name, language="en") if profile else None)
    service.repository = repo or Repo()
    service.generator = generator or Generator()
    return service


def refused(call, status):
    with pytest.raises(HTTPException) as caught:
        run(call)

    assert caught.value.status_code == status


# ---- reading ---------------------------------------------------------------------------------------------------------------------


def test_the_portfolio_page_data_has_projects_checklist_and_suggestions():
    service = make(Repo(projects=[stored_project()]))
    result = run(service.get(uuid4()))

    assert len(result.projects) == 1 and len(result.checklist) == 6
    assert result.suggestions[0].title == "Build an API" and result.is_public is False
    assert service.db.commits == 1  # a first visit creates the empty portfolio


def test_everything_needs_a_profile():
    service = make(profile=False)

    for call in (
        service.get(uuid4()), service.update(UpdatePortfolioRequest(), uuid4()),
        service.create_project(CreateProjectRequest(title="x"), uuid4()),
        service.delete_project(uuid4(), uuid4()), service.draft_description(uuid4(), uuid4()),
    ):
        refused(call, 404)


def test_a_database_conflict_becomes_a_409_not_a_crash():
    service = make(db=Db(commit_error=IntegrityError("insert", {}, Exception("duplicate"))))
    refused(service.get(uuid4()), 409)

    assert service.db.rollbacks == 1


# ---- publishing ---------------------------------------------------------------------------------------------------------------------


def test_text_fields_are_saved_and_achievements_are_checked(quiet):
    repo = Repo()
    result = run(make(repo).update(UpdatePortfolioRequest(headline="Backend dev", bio="Hi"), uuid4()))

    assert (repo.portfolio.headline, repo.portfolio.bio) == ("Backend dev", "Hi")
    assert result.headline == "Backend dev" and len(quiet.evaluated) == 1


def test_publishing_gives_an_address_and_reports_it(quiet):
    repo = Repo()
    run(make(repo).update(UpdatePortfolioRequest(is_public=True), uuid4()))

    assert repo.portfolio.is_public is True and repo.portfolio.slug.startswith("rohan-")
    assert quiet.events == ["portfolio_published"]


def test_publishing_keeps_an_address_that_was_already_chosen(quiet):
    repo = Repo()
    repo.portfolio.slug = "my-own-name"
    run(make(repo).update(UpdatePortfolioRequest(is_public=True), uuid4()))

    assert repo.portfolio.slug == "my-own-name"


def test_unpublishing_keeps_the_address_and_is_reported(quiet):
    repo = Repo()
    repo.portfolio.slug, repo.portfolio.is_public = "keep-me", True
    run(make(repo).update(UpdatePortfolioRequest(is_public=False), uuid4()))

    assert repo.portfolio.is_public is False and repo.portfolio.slug == "keep-me"
    assert quiet.events == ["portfolio_unpublished"]


def test_a_taken_address_is_a_conflict_and_changes_nothing():
    repo = Repo(taken={"rohan-dev"})
    refused(make(repo).update(UpdatePortfolioRequest(slug="rohan-dev"), uuid4()), 409)

    assert repo.portfolio.slug is None


def test_when_no_free_address_can_be_found_it_says_so(quiet):
    repo = Repo()

    async def always_taken(slug, except_profile_id):
        return True

    repo.slug_taken = always_taken
    refused(make(repo).update(UpdatePortfolioRequest(is_public=True), uuid4()), 500)


def test_fields_not_sent_are_left_alone():
    repo = Repo()
    repo.portfolio.headline = "Keep"
    run(make(repo).update(UpdatePortfolioRequest(bio="New bio"), uuid4()))

    assert repo.portfolio.headline == "Keep"


# ---- checklist ----------------------------------------------------------------------------------------------------------------------


def test_ticking_a_checklist_item_keeps_the_others():
    repo = Repo()
    repo.portfolio.checklist = {"readme": True}
    result = run(make(repo).set_checklist(ChecklistUpdateRequest(item_id="live", done=True), uuid4()))

    assert {i.id for i in result.checklist if i.done} == {"readme", "live"}


def test_unticking_works():
    repo = Repo()
    repo.portfolio.checklist = {"readme": True}
    result = run(make(repo).set_checklist(ChecklistUpdateRequest(item_id="readme", done=False), uuid4()))

    assert not any(i.done for i in result.checklist)


# ---- projects -----------------------------------------------------------------------------------------------------------------------


def test_a_manual_project_gets_sensible_defaults():
    repo = Repo()
    result = run(make(repo).create_project(CreateProjectRequest(title="Todo API"), uuid4()))

    assert result.title == "Todo API" and result.tech == [] and result.visible is True
    assert repo.projects[0].position == 0


def test_projects_are_placed_after_the_existing_ones():
    repo = Repo(projects=[stored_project(), stored_project()])
    run(make(repo).create_project(CreateProjectRequest(title="Third"), uuid4()))

    assert repo.projects[-1].position == 2


def test_a_learner_cannot_add_more_than_the_limit():
    repo = Repo(projects=[stored_project() for _ in range(MAX_PROJECTS)])
    refused(make(repo).create_project(CreateProjectRequest(title="One too many"), uuid4()), 409)


def test_an_explicit_title_beats_the_lessons_title():
    unit = SimpleNamespace(id=uuid4(), title="Lesson title", description="Lesson brief", completed=True)
    repo = Repo(unit=(unit, SimpleNamespace(title="REST APIs")))
    result = run(make(repo).create_project(CreateProjectRequest(title="My name", source_unit_id=unit.id), uuid4()))

    assert result.title == "My name" and result.description == "Lesson brief"


def test_editing_a_project_changes_only_what_was_sent():
    mine = stored_project(description="old")
    result = run(make(Repo(projects=[mine])).update_project(mine.id, ProjectFields(title="Renamed"), uuid4()))

    assert result.title == "Renamed" and result.description == "old"


def test_the_description_and_links_can_be_cleared_but_the_title_cannot():
    mine = stored_project(description="old", repo_url="https://github.com/x/y")
    service = make(Repo(projects=[mine]))
    run(service.update_project(mine.id, ProjectFields(description=None, repo_url=None), uuid4()))

    assert mine.description is None and mine.repo_url is None
    refused(service.update_project(mine.id, ProjectFields(title=None), uuid4()), 422)
    refused(service.update_project(mine.id, ProjectFields(visible=None), uuid4()), 422)
    refused(service.update_project(mine.id, ProjectFields(tech=None), uuid4()), 422)


def test_another_learners_project_is_a_404_to_edit_delete_or_describe():
    service = make(Repo())

    refused(service.update_project(uuid4(), ProjectFields(title="x"), uuid4()), 404)
    refused(service.delete_project(uuid4(), uuid4()), 404)
    refused(service.draft_description(uuid4(), uuid4()), 404)


def test_deleting_a_project_removes_it():
    mine = stored_project()
    repo = Repo(projects=[mine])
    run(make(repo).delete_project(mine.id, uuid4()))

    assert repo.deleted is mine and repo.projects == []


# ---- the AI description ------------------------------------------------------------------------------------------------------------


def test_a_description_is_drafted_from_the_project_and_its_lesson():
    unit = SimpleNamespace(id=uuid4(), title="t", description="short", content="Build it in 5 steps", completed=True)
    mine = stored_project(title="Todo API", source_unit_id=unit.id, tech=["python", "fastapi"])
    generator = Generator("Built a REST API.")
    service = make(Repo(projects=[mine], unit=(unit, SimpleNamespace(title="REST APIs"))), generator=generator)
    result = run(service.draft_description(mine.id, uuid4()))

    assert result.description == "Built a REST API."
    assert generator.seen == {"title": "Todo API", "tech": ["python", "fastapi"], "task_title": "REST APIs",
                              "brief": "Build it in 5 steps"}


def test_a_project_without_a_lesson_is_described_from_its_own_facts():
    mine = stored_project(title="Portfolio site")
    generator = Generator()
    run(make(Repo(projects=[mine]), generator=generator).draft_description(mine.id, uuid4()))

    assert generator.seen["task_title"] is None and generator.seen["brief"] is None


def test_an_ai_failure_is_a_502():
    mine = stored_project()
    service = make(Repo(projects=[mine]), generator=Generator(error=RuntimeError("model down")))
    refused(service.draft_description(mine.id, uuid4()), 502)


# ---- the public page ----------------------------------------------------------------------------------------------------------------


def test_the_public_page_shows_only_visible_projects_and_looks_up_the_address_in_lowercase():
    portfolio = SimpleNamespace(headline="Backend dev", bio="Hi")
    owner = SimpleNamespace(id=uuid4(), full_name="Sana Khan")
    repo = Repo(projects=[stored_project("Shown"), stored_project("Hidden", visible=False)], public=(portfolio, owner))
    result = run(make(repo).public("Sana-1A2B"))

    assert repo.asked_slug == "sana-1a2b"
    assert result.name == "Sana Khan" and [p.title for p in result.projects] == ["Shown"]


def test_a_nameless_owner_is_shown_as_learner():
    portfolio = SimpleNamespace(headline=None, bio=None)
    repo = Repo(public=(portfolio, SimpleNamespace(id=uuid4(), full_name=None)))

    assert run(make(repo).public("x-1234")).name == "Learner"


def test_a_missing_or_private_portfolio_is_the_same_404():
    refused(make(Repo(public=None)).public("nobody"), 404)
