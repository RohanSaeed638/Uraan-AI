import asyncio
import selectors
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.ai.services.career_recommender import catalogue_lines, pick_valid
from app.core.career_catalog import catalog_slugs, load_catalog
from app.models.career import Career
from app.repositories.career_repository import CareerRepository
from app.schemas.profile import CAREER_SLUG
from app.services.career_seed import seed_careers
from app.services.career_service import CareerService

LEVELS = {"beginner", "intermediate", "advanced"}
DEMANDS = {"low", "medium", "high", "very_high"}


# ---- the catalogue file ----------------------------------------------------


def test_catalogue_has_the_fourteen_prd_careers():
    assert len(load_catalog()) == 14
    assert len(catalog_slugs()) == 14


def test_every_catalogue_slug_is_a_valid_career_address():
    """Whether a career exists is checked against the database (admins can add
    careers); the schema only checks the address is well formed."""
    assert all(CAREER_SLUG.match(slug) for slug in catalog_slugs())
    assert not CAREER_SLUG.match("Not a slug!")


@pytest.mark.parametrize("career", load_catalog(), ids=lambda c: c["slug"])
def test_every_career_is_complete_and_sane(career):
    assert career["difficulty"] in LEVELS
    assert career["market_demand"] in DEMANDS
    assert 0 < career["estimated_months"] <= 36
    assert 0 < career["salary_min_pkr"] < career["salary_max_pkr"]
    assert len(career["description"]) > 60
    assert career["color"].startswith("#")
    assert len(career["skills"]) >= 5
    assert len(career["skills"]) == len(set(career["skills"]))
    assert len(career["resources"]) >= 3

    for resource in career["resources"]:
        assert resource["url"].startswith("https://")
        assert resource["type"] in {"course", "video", "docs", "book", "practice"}


# ---- AI picks stay inside the catalogue ------------------------------------

ALLOWED = {"backend-engineer", "ai-engineer", "data-scientist"}


def test_invented_careers_are_dropped():
    raw = {
        "recommendations": [
            {"slug": "quantum-wizard", "reason": "Sounds fun."},
            {"slug": "ai-engineer", "reason": "You like AI."},
        ]
    }

    assert pick_valid(raw, ALLOWED) == [{"slug": "ai-engineer", "reason": "You like AI."}]


def test_duplicates_blank_reasons_and_junk_are_dropped():
    raw = {
        "recommendations": [
            {"slug": "backend-engineer", "reason": "APIs suit you."},
            {"slug": "backend-engineer", "reason": "Again."},
            {"slug": "data-scientist", "reason": "  "},
            "nonsense",
        ]
    }

    assert [p["slug"] for p in pick_valid(raw, ALLOWED)] == ["backend-engineer"]


def test_at_most_three_picks():
    allowed = {f"c{i}" for i in range(6)}
    raw = {"recommendations": [{"slug": f"c{i}", "reason": "ok"} for i in range(6)]}

    assert len(pick_valid(raw, allowed)) == 3


def test_malformed_ai_output_gives_no_picks():
    assert pick_valid(["not", "a", "dict"], ALLOWED) == []
    assert pick_valid({"recommendations": "x"}, ALLOWED) == []


def test_catalogue_lines_list_every_slug():
    careers = [
        SimpleNamespace(
            slug=c["slug"], name=c["name"], difficulty=c["difficulty"],
            market_demand=c["market_demand"], estimated_months=c["estimated_months"],
            description=c["description"],
        )
        for c in load_catalog()
    ]
    text = catalogue_lines(careers)

    assert all(c["slug"] in text for c in load_catalog())


# ---- service rules (fakes) --------------------------------------------------


class FakeRepo:
    def __init__(self, careers):
        self.careers = {c.slug: c for c in careers}

    async def get_many(self, slugs):
        return {s: self.careers[s] for s in slugs if s in self.careers}

    async def list_active(self):
        return list(self.careers.values())

    async def get_by_slug(self, slug):
        return self.careers.get(slug)


class FakeProfiles:
    def __init__(self, profile):
        self.profile = profile

    async def get_by_auth_user_id(self, _):
        return self.profile


class FakeRecommender:
    def __init__(self, picks=None, boom=False):
        self.picks, self.boom, self.seen = picks or [], boom, None

    async def recommend(self, careers, answers):
        self.seen = answers
        if self.boom:
            raise RuntimeError("provider down")
        return self.picks


def career(slug):
    return SimpleNamespace(slug=slug, id=uuid4(), name=slug)


def service(careers, recommender=None, profile=None):
    svc = CareerService(db=None, recommender=recommender or FakeRecommender())
    svc.repository = FakeRepo(careers)
    svc.profiles = FakeProfiles(profile)
    return svc


def status_of(coro):
    with pytest.raises(HTTPException) as info:
        asyncio.run(coro)
    return info.value.status_code


def test_compare_needs_two_different_careers():
    svc = service([career("a"), career("b")])

    assert status_of(svc.compare(["a", "a"])) == 422


def test_compare_unknown_career_is_404():
    svc = service([career("a"), career("b")])

    assert status_of(svc.compare(["a", "zzz"])) == 404


def test_compare_keeps_the_requested_order():
    svc = service([career("a"), career("b"), career("c")])

    result = asyncio.run(svc.compare(["c", "a"]))

    assert [c.slug for c in result["careers"]] == ["c", "a"]


def test_unknown_filter_values_are_rejected():
    svc = service([])

    assert status_of(svc.search(difficulty="expert", page=1, page_size=20)) == 422
    assert status_of(svc.search(demand="huge", page=1, page_size=20)) == 422


def test_recommend_fills_gaps_from_the_profile():
    rec = FakeRecommender(picks=[{"slug": "a", "reason": "fits"}])
    profile = SimpleNamespace(id=uuid4(), language="en", education="college", daily_hours=3, learning_goal="a job")
    svc = service([career("a")], rec, profile)

    result = asyncio.run(svc.recommend(uuid4(), {"interests": "apis"}))

    assert rec.seen["education"] == "college"
    assert rec.seen["daily_hours"] == 3
    assert rec.seen["goal"] == "a job"
    assert result["recommendations"][0]["reason"] == "fits"


def test_typed_answers_beat_the_profile():
    rec = FakeRecommender(picks=[{"slug": "a", "reason": "fits"}])
    profile = SimpleNamespace(id=uuid4(), language="en", education="college", daily_hours=3, learning_goal="x")
    svc = service([career("a")], rec, profile)

    asyncio.run(svc.recommend(uuid4(), {"interests": "apis", "daily_hours": 5}))

    assert rec.seen["daily_hours"] == 5


def test_provider_failure_and_empty_picks_are_a_502():
    assert status_of(
        service([career("a")], FakeRecommender(boom=True)).recommend(uuid4(), {"interests": "x"})
    ) == 502
    assert status_of(
        service([career("a")], FakeRecommender(picks=[])).recommend(uuid4(), {"interests": "x"})
    ) == 502


# ---- real database, rolled back ----------------------------------------------


def _with_db(fn):
    from app.core.config import settings

    async def run():
        engine = create_async_engine(settings.DATABASE_URL)
        try:
            async with engine.connect() as conn:
                trans = await conn.begin()
                db = AsyncSession(bind=conn, join_transaction_mode="create_savepoint")
                try:
                    return await fn(db)
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


def test_real_db_seed_is_idempotent_and_filters_work():
    async def check(db):
        catalog = load_catalog()

        await seed_careers(db, catalog)
        again = await seed_careers(db, catalog)
        assert again == {"created": 0, "updated": 14}

        repo = CareerRepository(db)

        rows, total = await repo.search(
            search=None, difficulty=None, demand=None, category=None,
            min_salary=None, max_salary=None, page=1, page_size=50,
        )
        assert total == 14 and len(rows) == 14

        beginners, _ = await repo.search(
            search=None, difficulty="beginner", demand=None, category=None,
            min_salary=None, max_salary=None, page=1, page_size=50,
        )
        assert beginners and all(c.difficulty == "beginner" for c in beginners)

        found, _ = await repo.search(
            search="figma", difficulty=None, demand=None, category=None,
            min_salary=None, max_salary=None, page=1, page_size=50,
        )
        assert [c.slug for c in found] == ["ui-ux-designer"]

        rich, _ = await repo.search(
            search=None, difficulty=None, demand=None, category=None,
            min_salary=500000, max_salary=None, page=1, page_size=50,
        )
        assert rich and all(c.salary_max_pkr >= 500000 for c in rich)

        page2, total2 = await repo.search(
            search=None, difficulty=None, demand=None, category=None,
            min_salary=None, max_salary=None, page=2, page_size=10,
        )
        assert total2 == 14 and len(page2) == 4

        detail = await repo.get_by_slug("backend-engineer")
        assert [s.name for s in detail.skills][0] == "Python"
        assert len(detail.resources) >= 3

        detail.is_active = False
        await db.flush()
        assert await repo.get_by_slug("backend-engineer") is None

        # skills are replaced, not duplicated, on a re-seed
        await seed_careers(db, catalog)
        from sqlalchemy import func, select
        from app.models.career import CareerSkill

        assert (
            await db.execute(select(func.count()).select_from(CareerSkill))
        ).scalar_one() == sum(len(c["skills"]) for c in catalog)

    _with_db(check)


# ---- roadmap template -----------------------------------------------------------


def test_template_lists_skills_in_order_and_preferred_resources():
    from app.ai.prompts.career_template import career_template

    c = SimpleNamespace(
        name="Backend Engineer",
        estimated_months=9,
        skills=[
            SimpleNamespace(name="SQL", order_number=2),
            SimpleNamespace(name="Python", order_number=1),
        ],
        resources=[
            SimpleNamespace(
                title="CS50P", provider="Harvard", type="course",
                url="https://cs50.harvard.edu/python/", order_number=1,
            )
        ],
    )

    text = career_template(c)

    assert text.index("1. Python") < text.index("2. SQL")
    assert "https://cs50.harvard.edu/python/" in text
    assert "do not drop a core skill" in text


def test_no_template_for_an_unknown_career():
    from app.ai.prompts.career_template import career_template

    assert career_template(None) == ""


def test_roadmap_prompt_formats_with_the_template():
    from app.ai.prompts.roadmap_prompt import ROADMAP_PROMPT

    text = ROADMAP_PROMPT.format(
        name="A", career="backend-engineer", career_stage="beginner",
        skill="beginner", learning_goal="job", learning_style="reading",
        daily_hours=2, duration=6, learner_context="",
        career_template="TEMPLATE-MARK",
    )

    assert "TEMPLATE-MARK" in text
