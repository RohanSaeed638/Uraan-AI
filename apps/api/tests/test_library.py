"""The resource library: ranking, rules, and the real database (rolled back)."""
import asyncio
import selectors
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.career_catalog import load_catalog
from app.models.profile import Profile
from app.repositories.library_repository import LibraryRepository
from app.services.career_seed import seed_careers, seed_library
from app.services.library_service import LibraryService, rank_for_task, words


def resource(title, provider="", avg=None):
    return {"title": title, "provider": provider, "avg_rating": avg}


# ---- ranking resources for a task -------------------------------------------------------


def test_words_ignore_filler():
    assert words("Learn the basics of Python") == {"python"}


def test_resources_sharing_words_with_the_task_come_first():
    items = [
        resource("Docker: Get Started", "Docker"),
        resource("FastAPI Tutorial", "FastAPI"),
        resource("PostgreSQL Tutorial", "PostgreSQL"),
    ]

    ranked = rank_for_task(items, "Build REST APIs with FastAPI", None, 3)

    assert ranked[0]["title"] == "FastAPI Tutorial"


def test_ties_go_to_the_better_rated_then_title():
    items = [resource("B guide", avg=3.0), resource("A guide", avg=None), resource("C guide", avg=4.5)]

    ranked = rank_for_task(items, "unrelated topic", None, 3)

    assert [r["title"] for r in ranked] == ["C guide", "B guide", "A guide"]


def test_limit_applies():
    assert len(rank_for_task([resource(f"r{i}") for i in range(9)], "x", None, 4)) == 4


# ---- service rules (fakes) -----------------------------------------------------------------


class FakeRepo:
    def __init__(self):
        self.calls = []

    async def get(self, profile_id, resource_id):
        return None if resource_id == "missing" else {"id": resource_id}

    async def add_bookmark(self, *args):
        pass

    async def set_rating(self, *args):
        pass


def service():
    svc = LibraryService(db=None)
    svc.repository = FakeRepo()

    async def profile(_):
        return SimpleNamespace(id=uuid4())

    svc.profiles = SimpleNamespace(get_by_auth_user_id=profile)
    return svc


def status_of(coro):
    with pytest.raises(HTTPException) as info:
        asyncio.run(coro)
    return info.value.status_code


FILTERS = dict(
    q=None, career=None, type=None, difficulty=None, free_only=False,
    bookmarked_only=False, sort="recommended", page=1, page_size=24,
)


@pytest.mark.parametrize(
    "over", [{"type": "magazine"}, {"difficulty": "expert"}, {"sort": "random"}]
)
def test_unknown_filter_values_are_rejected(over):
    assert status_of(service().search(uuid4(), **{**FILTERS, **over})) == 422


def test_bookmarking_a_missing_resource_is_404():
    assert status_of(service().bookmark(uuid4(), "missing")) == 404
    assert status_of(service().rate(uuid4(), "missing", 5)) == 404


# ---- the real database ---------------------------------------------------------------------------


def with_db(fn):
    from app.core.config import settings

    async def run():
        engine = create_async_engine(settings.DATABASE_URL)
        try:
            async with engine.connect() as conn:
                trans = await conn.begin()
                db = AsyncSession(
                    bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False
                )
                try:
                    profile = Profile(auth_user_id=uuid4(), full_name="Tester")
                    db.add(profile)
                    await db.flush()
                    return await fn(db, profile)
                finally:
                    await db.close()
                    await trans.rollback()
        finally:
            await engine.dispose()

    try:
        return asyncio.run(
            run(),
            loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()),
        )
    except OSError as exc:
        pytest.skip(f"database not reachable: {type(exc).__name__}")


def test_real_db_seed_search_bookmark_and_rate():
    async def check(db, profile):
        catalog = load_catalog()
        await seed_careers(db, catalog)
        await seed_library(db, catalog)
        again = await seed_library(db, catalog)
        assert again["created"] == 0 and again["updated"] > 40  # idempotent

        svc = LibraryService(db)
        uid, repo = profile.auth_user_id, LibraryRepository(db)

        everything = await svc.search(uid, **{**FILTERS, "page_size": 50})
        assert everything["total"] >= 50

        # a resource shared by two careers lists both
        shared = [r for r in everything["items"] if len(r["career_slugs"]) > 1]
        assert shared

        designers = await svc.search(uid, **{**FILTERS, "career": "video-editor"})
        assert designers["total"] == 3 and all("video-editor" in r["career_slugs"] for r in designers["items"])

        courses = await svc.search(uid, **{**FILTERS, "type": "course", "free_only": True, "difficulty": "beginner"})
        assert courses["total"] > 0
        assert all(r["type"] == "course" and r["is_free"] and r["difficulty"] == "beginner" for r in courses["items"])

        found = await svc.search(uid, **{**FILTERS, "q": "figma"})
        assert [r["provider"] for r in found["items"]] == ["Figma"]

        target = designers["items"][0]["id"]

        # bookmark: idempotent, visible to me, filterable
        for _ in range(2):
            marked = await svc.bookmark(uid, target)
        assert marked["bookmarked"] is True
        saved = await svc.search(uid, **{**FILTERS, "bookmarked_only": True})
        assert [r["id"] for r in saved["items"]] == [target]
        assert (await svc.unbookmark(uid, target))["bookmarked"] is False

        # rating: one per learner, changeable, averaged, removable
        rated = await svc.rate(uid, target, 4)
        assert (rated["my_rating"], rated["avg_rating"], rated["rating_count"]) == (4, 4.0, 1)
        rated = await svc.rate(uid, target, 2)
        assert (rated["my_rating"], rated["avg_rating"], rated["rating_count"]) == (2, 2.0, 1)

        other = Profile(auth_user_id=uuid4(), full_name="Other")
        db.add(other)
        await db.flush()
        await repo.set_rating(other.id, target, 5)

        mine = await repo.get(profile.id, target)
        theirs = await repo.get(other.id, target)
        assert (mine["avg_rating"], mine["rating_count"], mine["my_rating"]) == (3.5, 2, 2)
        assert theirs["my_rating"] == 5 and theirs["bookmarked"] is False  # not shared

        cleared = await svc.clear_rating(uid, target)
        assert cleared["my_rating"] is None and cleared["rating_count"] == 1

        # best rated first
        top = await svc.search(uid, **{**FILTERS, "career": "video-editor"})
        assert top["items"][0]["id"] == target

        # an out-of-range rating cannot reach the table
        with pytest.raises(Exception):
            await repo.set_rating(profile.id, target, 9)
            await db.flush()

    with_db(check)
