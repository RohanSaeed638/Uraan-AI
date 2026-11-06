"""The admin numbers: lesson quality, the sign-up funnel, AI usage. Real database, rolled back."""
import asyncio
import selectors
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import llm
from app.ai.llm.types import AIBudgetExceeded
from app.ai.pricing import estimate_cost
from app.api.dependencies import get_current_user
from app.api.routes.admin_insights import router as insights_router
from app.core.config import settings
from app.db.base import get_db
from app.db.session import engine
from app.models.ai_request import AiRequest
from app.models.enums import CareerStage, LearningStyle, RoadmapStatus, SkillLevel
from app.models.feedback import LessonFeedback
from app.models.learning_activity import LearningActivity
from app.models.link_check import LinkCheck
from app.models.profile import Profile
from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.models.task_learning_unit import LearningUnitType, TaskLearningUnit
from app.services.insights_service import InsightsService, percent


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


async def person(db, conn, name="Learner", role="student", created=None, onboarded=False):
    auth_id = uuid4()
    await conn.execute(text("insert into auth.users (id, email) values (:i, :e)"), {"i": auth_id, "e": f"{auth_id}@x.test"})
    values = dict(auth_user_id=auth_id, full_name=name, daily_hours=1, xp=0, streak_days=0, language="en",
                  role=role, onboarding_completed=onboarded)

    if created:
        values["created_at"] = created

    me = Profile(**values)
    db.add(me)
    await db.flush()

    return auth_id, me


async def roadmap_with_lesson(db, me, status=RoadmapStatus.ACTIVE):
    roadmap = Roadmap(
        profile_id=me.id, title="Plan", description="d", status=status, career_slug="backend-engineer",
        career_stage=CareerStage.BEGINNER, skill_level=SkillLevel.BEGINNER, learning_goal="job",
        learning_style=LearningStyle.READING, daily_hours=1, target_duration=6,
    )
    db.add(roadmap)
    await db.flush()
    phase = RoadmapPhase(roadmap_id=roadmap.id, order=1, title="P", description="d", duration_weeks=2)
    db.add(phase)
    await db.flush()
    task = RoadmapTask(phase_id=phase.id, title="T", order=1, completed=False)
    db.add(task)
    await db.flush()
    unit = TaskLearningUnit(task_id=task.id, day=1, order=1, type=LearningUnitType.READING, title="L",
                            estimated_minutes=10, completed=False, status="ready")
    db.add(unit)
    await db.flush()

    return unit


def vote(me, helpful, topic="Learn HTTP", career="backend-engineer", reason=None, comment=None, when=None):
    row = LessonFeedback(profile_id=me.id, helpful=helpful, reason=reason, comment=comment, career_slug=career,
                         task_title=topic, lesson_title="A lesson", lesson_type="reading")

    if when:
        row.created_at = when

    return row


# ---- lesson quality -------------------------------------------------------------------------------------------------------


def test_percent_is_one_decimal_and_safe_with_nothing():
    assert percent(1, 3) == 33.3 and percent(0, 5) == 0.0 and percent(5, 0) is None


def test_the_feedback_overview_adds_votes_up_by_reason_career_and_topic():
    async def check(db, conn):
        _, a = await person(db, conn, "A")
        _, b = await person(db, conn, "B")
        _, c = await person(db, conn, "C")
        db.add_all([
            vote(a, False, "Learn HTTP", reason="wrong", comment="Verb table is wrong"),
            vote(b, False, "learn http", reason="wrong"),
            vote(c, True, "Learn HTTP"),
            vote(a, False, "Design systems", career="ui-ux-designer", reason="too_hard"),
            vote(b, True, "Design systems", career="ui-ux-designer"),
            vote(c, False, "Old topic", reason="unclear", when=datetime.now(timezone.utc) - timedelta(days=90)),
        ])
        await db.flush()

        return await InsightsService(db).feedback(30)

    result = with_db(check)

    # (The database may hold real votes too, so compare what these rows add.)
    topics = {(t["task_title"].lower(), t["career_slug"]): t for t in result["topics"]}
    assert topics[("learn http", "backend-engineer")]["not_helpful"] >= 2
    assert topics[("learn http", "backend-engineer")]["helpful"] >= 1
    assert ("old topic", "backend-engineer") not in topics  # outside the 30 days
    assert {r["reason"] for r in result["by_reason"]} >= {"wrong", "too_hard"}
    assert any(c["career_slug"] == "ui-ux-designer" for c in result["by_career"])
    assert any(r["comment"] == "Verb table is wrong" for r in result["recent"])
    assert "Old topic" not in {r["task_title"] for r in result["recent"]}
    assert result["total"] == result["helpful"] + result["not_helpful"]


def test_only_not_helpful_votes_are_in_the_recent_list():
    async def check(db, conn):
        _, a = await person(db, conn)
        db.add_all([vote(a, True, topic="Praised only"), vote(a, False, topic="Criticised", reason="wrong")])
        await db.flush()

        return await InsightsService(db).feedback(30)

    recent = with_db(check)["recent"]

    assert "Praised only" not in {item["task_title"] for item in recent}
    assert "Criticised" in {item["task_title"] for item in recent}


# ---- the funnel ---------------------------------------------------------------------------------------------------------


def test_the_funnel_counts_how_far_each_new_learner_got_and_leaves_staff_out():
    async def check(db, conn):
        week_ago = datetime.now(timezone.utc) - timedelta(days=12)
        _, active = await person(db, conn, "Active", created=week_ago, onboarded=True)
        _, quiet = await person(db, conn, "Quiet", created=week_ago)
        _, stopped = await person(db, conn, "Stopped", created=week_ago, onboarded=True)
        _, staff = await person(db, conn, "Staff", role="admin", created=week_ago, onboarded=True)
        first = await roadmap_with_lesson(db, active)
        second = await roadmap_with_lesson(db, active)
        await roadmap_with_lesson(db, stopped)
        await roadmap_with_lesson(db, staff)
        # "Active" learned something at once and again 9 days later: they came back.
        for unit, when in ((first, week_ago + timedelta(hours=1)), (second, week_ago + timedelta(days=9))):
            db.add(LearningActivity(profile_id=active.id, learning_unit_id=unit.id, activity_type="completed",
                                    estimated_minutes=10, created_at=when))
        await db.flush()

        return await InsightsService(db).funnel(8)

    result = with_db(check)
    steps = {s["key"]: s for s in result["steps"]}

    assert steps["signups"]["count"] >= 3
    # Each step is a subset of the one before it.
    assert steps["onboarded"]["count"] <= steps["signups"]["count"]
    assert steps["roadmap"]["count"] >= 2  # Active and Stopped have a roadmap; Staff is left out
    assert steps["first_lesson"]["count"] >= 1 and steps["returned"]["count"] >= 1
    assert steps["returned"]["count"] <= result["eligible_for_return"]
    assert all(set(c) >= {"week", "signups", "onboarded", "roadmap", "first_lesson", "returned", "finished"} for c in result["cohorts"])


def test_the_funnel_excludes_staff_exactly():
    async def check(db, conn):
        when = datetime.now(timezone.utc) - timedelta(days=30)
        baseline = (await InsightsService(db).funnel(52))["steps"][0]["count"]
        await person(db, conn, "Staff", role="admin", created=when)
        after_staff = (await InsightsService(db).funnel(52))["steps"][0]["count"]
        await person(db, conn, "Learner", created=when)
        after_learner = (await InsightsService(db).funnel(52))["steps"][0]["count"]

        return baseline, after_staff, after_learner

    baseline, after_staff, after_learner = with_db(check)

    assert after_staff == baseline and after_learner == baseline + 1


def test_a_learner_who_signed_up_a_few_days_ago_is_not_yet_counted_as_able_to_return():
    async def check(db, conn):
        before = (await InsightsService(db).funnel(8))["eligible_for_return"]
        await person(db, conn, "Brand new", created=datetime.now(timezone.utc) - timedelta(days=2))
        after = (await InsightsService(db).funnel(8))["eligible_for_return"]

        return before, after

    before, after = with_db(check)

    assert before == after


# ---- AI usage and spend -------------------------------------------------------------------------------------------------


def request(me, model="gpt-4.1-mini", provider="openai", purpose="lessons", ok=True, t_in=1000, t_out=500):
    return AiRequest(profile_id=me.id if me else None, purpose=purpose, provider=provider, model=model,
                     success=ok, input_tokens=t_in, output_tokens=t_out, latency_ms=100)


def test_costs_are_estimated_from_tokens_and_unknown_models_are_unpriced(monkeypatch):
    monkeypatch.setattr(settings, "AI_PRICES", "")

    assert estimate_cost("gpt-4.1-mini", 1_000_000, 500_000) == pytest.approx(0.40 + 0.80)
    assert estimate_cost("gpt-4.1-mini", None, None) == 0.0
    assert estimate_cost("some-new-model", 1000, 1000) is None


def test_prices_can_be_added_or_overridden_from_settings(monkeypatch):
    monkeypatch.setattr(settings, "AI_PRICES", '{"some-new-model": [2, 4], "gpt-4.1-mini": [1, 1]}')

    assert estimate_cost("some-new-model", 1_000_000, 1_000_000) == pytest.approx(6.0)
    assert estimate_cost("gpt-4.1-mini", 1_000_000, 0) == pytest.approx(1.0)


def test_a_broken_price_setting_is_ignored_not_fatal(monkeypatch):
    monkeypatch.setattr(settings, "AI_PRICES", "not json at all")

    assert estimate_cost("gpt-4.1-mini", 1_000_000, 0) == pytest.approx(0.40)


def test_ai_usage_adds_up_calls_tokens_failures_and_who_uses_most(monkeypatch):
    monkeypatch.setattr(settings, "AI_PRICES", "")

    async def check(db, conn):
        _, heavy = await person(db, conn, "Heavy User")
        _, light = await person(db, conn, "Light User")
        db.add_all([
            request(heavy, t_in=2_000_000, t_out=1_000_000),
            request(heavy, ok=False, t_in=100, t_out=0),
            request(light, model="mystery-model", provider="other", purpose="mentor", t_in=5000, t_out=5000),
        ])
        await db.flush()
        usage = await InsightsService(db).ai_usage(7)

        return usage

    usage = with_db(check)
    models = {(m["provider"], m["model"]): m for m in usage["by_model"]}

    assert models[("openai", "gpt-4.1-mini")]["requests"] >= 2 and models[("openai", "gpt-4.1-mini")]["failed"] >= 1
    assert models[("openai", "gpt-4.1-mini")]["estimated_cost_usd"] >= 0.8 + 1.6  # 2M in + 1M out
    assert models[("other", "mystery-model")]["estimated_cost_usd"] is None
    assert usage["unpriced_tokens"] >= 10_000
    assert {p["purpose"] for p in usage["by_purpose"]} >= {"lessons", "mentor"}
    assert [u["name"] for u in usage["top_users"]][0] == "Heavy User"
    assert usage["daily"] and usage["requests"] == sum(m["requests"] for m in usage["by_model"])


# ---- the daily limit --------------------------------------------------------------------------------------------------------


def run(coro):
    return asyncio.run(coro, loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))


def test_no_limit_means_no_check(monkeypatch):
    monkeypatch.setattr(settings, "AI_DAILY_TOKENS_PER_USER", 0)

    async def explode(profile_id):
        raise AssertionError("must not be counted")

    monkeypatch.setattr(llm, "tokens_used_today", explode)

    run(llm.check_budget(uuid4()))


def test_a_learner_over_their_allowance_is_refused_like_an_outage(monkeypatch):
    monkeypatch.setattr(settings, "AI_DAILY_TOKENS_PER_USER", 1000)

    async def used(profile_id):
        return 1000

    monkeypatch.setattr(llm, "tokens_used_today", used)

    with pytest.raises(AIBudgetExceeded) as caught:
        run(llm.check_budget(uuid4()))

    assert isinstance(caught.value, llm.AIUnavailableError)


def test_under_the_allowance_calls_go_through_and_calls_without_a_learner_are_never_limited(monkeypatch):
    monkeypatch.setattr(settings, "AI_DAILY_TOKENS_PER_USER", 1000)

    async def used(profile_id):
        return 999

    monkeypatch.setattr(llm, "tokens_used_today", used)
    run(llm.check_budget(uuid4()))
    run(llm.check_budget(None))


def test_if_counting_fails_the_call_is_allowed(monkeypatch):
    monkeypatch.setattr(settings, "AI_DAILY_TOKENS_PER_USER", 1000)

    async def broken(profile_id):
        raise RuntimeError("database down")

    monkeypatch.setattr(llm, "tokens_used_today", broken)
    run(llm.check_budget(uuid4()))


def test_the_count_comes_from_todays_calls_only(monkeypatch):
    import app.db.session as session_module

    async def check(db, conn):
        _, me = await person(db, conn)
        old = request(me, t_in=500, t_out=500)
        old.created_at = datetime.now(timezone.utc) - timedelta(days=2)
        db.add_all([request(me, t_in=300, t_out=200), old])
        await db.flush()

        class Same:
            """The helper opens its own session; hand it this test's (rolled back) one."""

            async def __aenter__(self):
                return db

            async def __aexit__(self, *exc):
                return False

        monkeypatch.setattr(session_module, "SessionLocal", lambda: Same())

        return await llm.tokens_used_today(me.id)

    assert with_db(check) == 500


# ---- only admins see any of it ----------------------------------------------------------------------------------------


def test_only_admins_can_read_the_numbers():
    async def check(db, conn):
        _, learner = await person(db, conn, "Plain", role="student")
        learner_auth = (await conn.execute(text("select auth_user_id from profiles where id = :p"), {"p": learner.id})).scalar_one()
        _, boss = await person(db, conn, "Boss", role="admin")
        boss_auth = (await conn.execute(text("select auth_user_id from profiles where id = :p"), {"p": boss.id})).scalar_one()

        api = FastAPI()
        api.include_router(insights_router)
        api.dependency_overrides[get_db] = lambda: db
        who = {"current": SimpleNamespace(id=learner_auth, email="plain@example.com")}
        api.dependency_overrides[get_current_user] = lambda: who["current"]
        statuses = {}

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://t") as client:
            for path in ("/admin/insights/feedback", "/admin/insights/funnel", "/admin/insights/ai-usage", "/admin/insights/links"):
                statuses[path] = [(await client.get(path)).status_code]
                who["current"] = SimpleNamespace(id=boss_auth, email="boss@example.com")
                statuses[path].append((await client.get(path)).status_code)
                who["current"] = SimpleNamespace(id=learner_auth, email="plain@example.com")

        return statuses

    for path, (learner_status, admin_status) in with_db(check).items():
        assert learner_status == 403, path
        assert admin_status == 200, path


def test_the_link_overview_counts_by_status_and_lists_the_dead_ones():
    async def check(db, conn):
        stamp = uuid4().hex[:8]
        db.add_all([
            LinkCheck(url=f"https://{stamp}.example/ok", status="ok", http_status=200, reason="", fail_count=0),
            LinkCheck(url=f"https://{stamp}.example/gone", status="dead", http_status=404, reason="page not found", fail_count=2),
            LinkCheck(url=f"https://{stamp}.example/blocked", status="unknown", http_status=403, reason="blocked", fail_count=0),
        ])
        await db.flush()

        return stamp, await InsightsService(db).links()

    stamp, overview = with_db(check)

    assert overview["ok"] >= 1 and overview["dead"] >= 1 and overview["unknown"] >= 1
    assert overview["last_checked"] is not None
    gone = [d for d in overview["dead_links"] if stamp in d["url"]]
    assert len(gone) == 1 and gone[0]["fail_count"] == 2 and gone[0]["http_status"] == 404
