"""The "download my data" export, against the real database (rolled back afterwards)."""
import asyncio
import json
import selectors
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.enums import CareerStage, LearningStyle, RoadmapStatus, SkillLevel
from app.models.portfolio import Portfolio, PortfolioProject
from app.models.profile import Profile
from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.services.account_service import AccountService

EXPECTED_SECTIONS = {
    "exported_at", "profile", "settings", "gamification", "roadmaps", "documents", "portfolio",
    "interviews", "mentor_conversations",
}


def with_db(fn):
    async def go():
        async with engine.connect() as conn:
            outer = await conn.begin()
            db = AsyncSession(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)

            try:
                return await fn(db, conn)
            finally:
                await db.close()
                await outer.rollback()

    try:
        return asyncio.run(go(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))
    except OSError:
        pytest.skip("database not reachable")


async def make_profile(db, conn, name="Export Test"):
    auth_id = uuid4()
    await conn.execute(text("insert into auth.users (id, email) values (:i, :e)"), {"i": auth_id, "e": f"{auth_id}@x.test"})
    me = Profile(auth_user_id=auth_id, full_name=name, daily_hours=1, xp=0, streak_days=0, language="en")
    db.add(me)
    await db.flush()
    return auth_id, me


def test_a_new_account_exports_every_section_even_when_empty():
    async def check(db, conn):
        auth_id, me = await make_profile(db, conn)
        return await AccountService(db).export(auth_id)

    data = with_db(check)

    assert set(data) == EXPECTED_SECTIONS
    assert data["profile"]["full_name"] == "Export Test"
    assert data["roadmaps"] == [] and data["documents"] == [] and data["interviews"] == []
    assert data["mentor_conversations"] == [] and data["portfolio"] is None and data["settings"] is None


def test_the_export_can_be_written_as_json():
    async def check(db, conn):
        auth_id, _ = await make_profile(db, conn)
        return await AccountService(db).export(auth_id)

    assert json.loads(json.dumps(with_db(check)))["profile"]["language"] == "en"


def test_roadmaps_are_exported_with_how_far_through_each_one_is():
    async def check(db, conn):
        auth_id, me = await make_profile(db, conn)
        roadmap = Roadmap(
            profile_id=me.id, title="My plan", description="d", status=RoadmapStatus.ACTIVE,
            career_slug="backend-engineer", career_stage=CareerStage.BEGINNER, skill_level=SkillLevel.BEGINNER,
            learning_goal="job", learning_style=LearningStyle.READING, daily_hours=1, target_duration=6,
        )
        db.add(roadmap)
        await db.flush()
        phase = RoadmapPhase(roadmap_id=roadmap.id, order=1, title="P", description="d", duration_weeks=2)
        db.add(phase)
        await db.flush()
        db.add_all(
            [
                RoadmapTask(phase_id=phase.id, title="done", order=1, completed=True),
                RoadmapTask(phase_id=phase.id, title="todo", order=2, completed=False),
            ]
        )
        await db.flush()
        return await AccountService(db).export(auth_id)

    plans = with_db(check)["roadmaps"]

    assert len(plans) == 1
    assert plans[0]["title"] == "My plan" and plans[0]["status"] == "active"
    assert (plans[0]["tasks_total"], plans[0]["tasks_completed"]) == (2, 1)
    assert plans[0]["skill_level"] == "beginner" and plans[0]["learning_style"] == "reading"


def test_the_portfolio_is_exported_with_its_checklist_and_projects():
    async def check(db, conn):
        auth_id, me = await make_profile(db, conn)
        db.add(Portfolio(profile_id=me.id, headline="Backend dev", bio="Hi", slug=f"s-{uuid4().hex[:8]}", is_public=True))
        db.add(
            PortfolioProject(
                profile_id=me.id, title="API", description="d", repo_url="https://github.com/x/y",
                tech=["python"], position=1, visible=True,
            )
        )
        await db.flush()
        return await AccountService(db).export(auth_id)

    portfolio = with_db(check)["portfolio"]

    assert portfolio["headline"] == "Backend dev" and portfolio["is_public"] is True
    assert portfolio["projects"][0]["tech"] == ["python"]
    assert portfolio["checklist"] and all(set(item) == {"id", "label", "done"} for item in portfolio["checklist"])


def test_only_the_owners_own_data_is_exported():
    async def check(db, conn):
        mine_auth, mine = await make_profile(db, conn, "Mine")
        _, other = await make_profile(db, conn, "Someone else")

        for owner, title in ((mine, "Mine"), (other, "Theirs")):
            db.add(
                Roadmap(
                    profile_id=owner.id, title=title, description="d", status=RoadmapStatus.ACTIVE,
                    career_slug="backend-engineer", career_stage=CareerStage.BEGINNER,
                    skill_level=SkillLevel.BEGINNER, learning_goal="job", learning_style=LearningStyle.READING,
                    daily_hours=1, target_duration=6,
                )
            )

        await db.flush()
        return await AccountService(db).export(mine_auth)

    data = with_db(check)

    assert [r["title"] for r in data["roadmaps"]] == ["Mine"]
    assert data["profile"]["full_name"] == "Mine"


def test_an_unknown_account_cannot_be_exported():
    async def check(db, conn):
        await AccountService(db).export(uuid4())

    with pytest.raises(HTTPException) as caught:
        with_db(check)

    assert caught.value.status_code == 404
