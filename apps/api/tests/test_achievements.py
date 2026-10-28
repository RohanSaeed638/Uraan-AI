"""Achievements, career titles, the monthly boss and the readiness score."""
import asyncio
import selectors
from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.achievement_catalog import (
    ACHIEVEMENTS,
    BOSS_BONUS_XP,
    TITLES,
    career_title,
)
from app.models.achievement import Achievement, BossChallenge, UserAchievement
from app.models.enums import CareerStage, LearningStyle, RoadmapStatus, SkillLevel
from app.models.notification import Notification
from app.models.profile import Profile
from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.models.task_learning_unit import LearningUnitType, TaskLearningUnit
from app.models.xp_event import XPEvent
from app.services.achievement_service import (
    AchievementService,
    days_left_in_month,
    measures,
    unlocked_by,
)
from app.services.gamification_service import GamificationService, level_for
from app.services.readiness import (
    WEIGHTS,
    ReadinessStats,
    compute_readiness,
    component_values,
    level_for_score,
)
from app.services.readiness_service import ReadinessService

# The unit tests replace `award` with a recorder (see conftest). These tests
# need the real one, so keep it from before that happens.
REAL_AWARD = GamificationService.award


@pytest.fixture(autouse=True)
def awards():
    """Replaces the shared fixture (which records awards instead of paying
    them): everything here uses the real XP and achievement code."""
    return None


# ---- the catalogue ---------------------------------------------------------------------------


KNOWN_RULES = {
    "lessons", "tasks", "projects", "hours", "quizzes_passed", "interviews", "documents",
    "mentor_chats", "roadmaps_completed", "portfolio_public", "bosses", "streak", "level",
}


def test_catalogue_is_consistent():
    codes = [a[0] for a in ACHIEVEMENTS]

    assert len(codes) == len(set(codes))
    assert all(len(code) <= 40 and code == code.lower() for code in codes)

    for code, title, description, category, icon, xp, rule, threshold in ACHIEVEMENTS:
        assert rule in KNOWN_RULES, code
        assert threshold >= 1 and xp >= 1, code
        assert title and description and icon, code
        assert category in {"learning", "streak", "projects", "practice", "career"}, code


def test_the_badges_asked_for_in_the_plan_exist():
    codes = {a[0] for a in ACHIEVEMENTS}

    assert {"first_lesson", "streak_7", "first_project", "hours_100", "first_quiz",
            "first_interview", "portfolio_published"} <= codes


def test_harder_badges_in_a_family_pay_more():
    by_rule: dict[str, list[tuple[int, int]]] = {}
    for *_, xp, rule, threshold in ACHIEVEMENTS:
        by_rule.setdefault(rule, []).append((threshold, xp))

    for rule, steps in by_rule.items():
        steps.sort()
        assert [xp for _, xp in steps] == sorted(xp for _, xp in steps), rule


# ---- career titles --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "xp, title",
    [(0, "Explorer"), (499, "Explorer"), (500, "Apprentice"), (1499, "Apprentice"),
     (1500, "Builder"), (3999, "Builder"), (4000, "Professional"), (9999, "Professional"),
     (10000, "Master"), (10**6, "Master"), (-50, "Explorer")],
)
def test_career_title_boundaries(xp, title):
    assert career_title(xp)["title"] == title


def test_the_titles_are_the_srs_ladder_in_order():
    assert [name for _, name in TITLES] == ["Explorer", "Apprentice", "Builder", "Professional", "Master"]
    assert [x for x, _ in TITLES] == sorted(x for x, _ in TITLES)


def test_progress_to_the_next_title():
    mid = career_title(250)

    assert (mid["next_title"], mid["xp_to_next"], mid["progress"]) == ("Apprentice", 250, 0.5)

    top = career_title(20000)

    assert top["next_title"] is None and top["xp_to_next"] is None and top["progress"] == 1.0


# ---- the rules -------------------------------------------------------------------------------------------


def row(**over):
    base = dict(lessons=0, projects=0, minutes=0, tasks=0, quizzes_passed=0, interviews=0,
                documents=0, mentor_chats=0, roadmaps_completed=0, portfolio_public=0, bosses=0)
    base.update(over)
    return base


def catalog_rows():
    return [
        SimpleNamespace(code=c, rule=r, threshold=t, is_active=True)
        for c, _, _, _, _, _, r, t in ACHIEVEMENTS
    ]


def test_measures_convert_minutes_to_hours_and_derive_the_level():
    stats = measures(row(minutes=630, portfolio_public=3), SimpleNamespace(streak_days=4, xp=450))

    assert stats["hours"] == 10.5
    assert stats["portfolio_public"] == 1  # published once, however many portfolios
    assert (stats["streak"], stats["level"]) == (4, level_for(450))


def test_a_new_learner_has_unlocked_nothing():
    stats = measures(row(), SimpleNamespace(streak_days=0, xp=0))

    assert unlocked_by(stats, catalog_rows(), set()) == []


def test_exactly_the_threshold_earns_a_badge():
    stats = measures(row(lessons=25, minutes=600), SimpleNamespace(streak_days=7, xp=0))

    codes = {a.code for a in unlocked_by(stats, catalog_rows(), set())}

    assert {"first_lesson", "lessons_25", "hours_10", "streak_3", "streak_7"} <= codes
    assert not codes & {"lessons_100", "streak_30", "hours_100"}


def test_badges_already_unlocked_are_not_repeated():
    stats = measures(row(lessons=1), SimpleNamespace(streak_days=0, xp=0))

    assert unlocked_by(stats, catalog_rows(), {"first_lesson"}) == []


def test_retired_badges_do_not_unlock():
    retired = SimpleNamespace(code="old", rule="lessons", threshold=1, is_active=False)

    assert unlocked_by({"lessons": 5}, [retired], set()) == []


@pytest.mark.parametrize(
    "today, left",
    [(date(2026, 10, 31), 1), (date(2026, 10, 1), 31), (date(2026, 11, 30), 1),
     (date(2028, 2, 29), 1), (date(2028, 2, 1), 29), (date(2027, 2, 1), 28)],
)
def test_days_left_in_the_month(today, left):
    assert days_left_in_month(today) == left


# ---- the readiness score ---------------------------------------------------------------------------------------


def stats(**over):
    return ReadinessStats(**over)


def test_the_weights_add_up_to_one_hundred():
    assert sum(WEIGHTS.values()) == 100
    assert WEIGHTS == {"tasks": 35, "projects": 20, "consistency": 15, "interviews": 15, "portfolio": 15}


def test_a_learner_who_has_done_nothing_scores_zero():
    result = compute_readiness(stats())

    assert result["score"] == 0 and result["level"] == "getting_started"
    assert all(c["points"] == 0 for c in result["components"])


def test_a_perfect_learner_scores_one_hundred():
    result = compute_readiness(stats(
        tasks_done=20, tasks_total=20, projects_done=4, projects_total=4, active_days=28,
        interviews_done=5, interview_avg_score=100, portfolio_public=True,
        portfolio_projects=6, portfolio_intro=True,
    ))

    assert result["score"] == 100 and result["level"] == "job_ready"
    assert result["tips"] == []


@pytest.mark.parametrize(
    "perfect, key",
    [
        (dict(tasks_done=10, tasks_total=10), "tasks"),
        (dict(projects_done=3, projects_total=3), "projects"),
        (dict(active_days=20), "consistency"),
        (dict(interviews_done=3, interview_avg_score=100), "interviews"),
        (dict(portfolio_public=True, portfolio_projects=3, portfolio_intro=True), "portfolio"),
    ],
)
def test_each_part_alone_is_worth_exactly_its_weight(perfect, key):
    result = compute_readiness(stats(**perfect))

    assert result["score"] == WEIGHTS[key]
    assert {c["key"]: c["points"] for c in result["components"]}[key] == WEIGHTS[key]


def test_half_the_tasks_is_seventeen_and_a_half_points():
    result = compute_readiness(stats(tasks_done=5, tasks_total=10))

    assert {c["key"]: c["points"] for c in result["components"]}["tasks"] == 17.5
    assert result["score"] == 18  # rounded for display


def test_consistency_is_capped_at_the_target():
    assert component_values(stats(active_days=28))["consistency"] == 1.0
    assert component_values(stats(active_days=10))["consistency"] == 0.5


def test_interviews_combine_practice_and_quality():
    assert component_values(stats(interviews_done=0, interview_avg_score=90))["interviews"] == 0
    assert component_values(stats(interviews_done=3, interview_avg_score=0))["interviews"] == 0.5
    assert component_values(stats(interviews_done=1, interview_avg_score=60))["interviews"] == pytest.approx(
        0.5 * (1 / 3) + 0.5 * 0.6
    )


def test_the_portfolio_counts_publishing_projects_and_an_intro():
    assert component_values(stats(portfolio_public=True))["portfolio"] == pytest.approx(0.4)
    assert component_values(stats(portfolio_projects=3))["portfolio"] == pytest.approx(0.4)
    assert component_values(stats(portfolio_intro=True))["portfolio"] == pytest.approx(0.2)
    assert component_values(stats(portfolio_projects=30))["portfolio"] == pytest.approx(0.4)


def test_nothing_planned_never_divides_by_zero():
    values = component_values(stats(tasks_total=0, projects_total=0))

    assert values["tasks"] == 0 and values["projects"] == 0


def test_values_never_leave_zero_to_one():
    values = component_values(stats(
        tasks_done=50, tasks_total=10, projects_done=9, projects_total=3, active_days=99,
        interviews_done=9, interview_avg_score=250, portfolio_projects=50,
    ))

    assert all(0 <= v <= 1 for v in values.values())


@pytest.mark.parametrize(
    "score, level",
    [(0, "getting_started"), (24, "getting_started"), (25, "building"), (49, "building"),
     (50, "almost_there"), (74, "almost_there"), (75, "job_ready"), (100, "job_ready")],
)
def test_readiness_levels(score, level):
    assert level_for_score(score) == level


def test_tips_point_at_the_biggest_gaps_first():
    result = compute_readiness(stats(
        tasks_done=10, tasks_total=10,   # full: no tip
        projects_done=0, projects_total=2,   # 20 points open
        active_days=20,                  # full
        interviews_done=0,               # 15 open
        portfolio_public=True, portfolio_projects=3, portfolio_intro=True,  # full
    ))

    assert [t["key"] for t in result["tips"]] == ["projects", "interviews"]
    assert result["tips"][0] == {"key": "projects", "action": "finish_projects", "count": 2, "href": "/projects"}
    assert result["tips"][1]["href"] == "/interview" and result["tips"][1]["count"] == 3


def test_at_most_three_tips():
    assert len(compute_readiness(stats())["tips"]) == 3


def test_tips_adapt_to_what_is_missing():
    no_plan = compute_readiness(stats())["tips"]
    assert no_plan[0]["key"] == "tasks" and no_plan[0]["action"] == "start_roadmap" and no_plan[0]["href"] == "/roadmaps"

    only_portfolio = compute_readiness(stats(
        tasks_done=1, tasks_total=1, projects_done=1, projects_total=1, active_days=20,
        interviews_done=3, interview_avg_score=100,
    ))["tips"]
    assert only_portfolio == [{"key": "portfolio", "action": "publish_portfolio", "count": 3, "href": "/portfolio"}]

    half = compute_readiness(stats(
        tasks_done=1, tasks_total=1, projects_done=1, projects_total=1, active_days=20,
        interviews_done=3, interview_avg_score=100, portfolio_public=True,
    ))["tips"]
    assert half[0]["action"] == "add_portfolio_projects"


# ---- the real database (rolled back) ------------------------------------------------------------------------------


def with_db(fn):
    from app.core.config import settings

    async def run():
        engine = create_async_engine(settings.DATABASE_URL)
        try:
            async with engine.connect() as conn:
                trans = await conn.begin()
                db = AsyncSession(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)
                try:
                    me = Profile(auth_user_id=uuid4(), full_name="Ayesha Khan", xp=0, streak_days=0)
                    db.add(me)
                    await db.flush()
                    return await fn(db, me)
                finally:
                    await db.close()
                    await trans.rollback()
        finally:
            await engine.dispose()

    try:
        return asyncio.run(run(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))
    except OSError as exc:
        pytest.skip(f"database not reachable: {type(exc).__name__}")


async def make_roadmap(db, profile, units, status=RoadmapStatus.ACTIVE):
    """A one-phase, one-task roadmap. `units`: (type, completed, minutes)."""
    roadmap = Roadmap(
        profile_id=profile.id, title="Plan", description="d", status=status,
        career_slug="backend-engineer", career_stage=CareerStage.BEGINNER,
        skill_level=SkillLevel.BEGINNER, learning_goal="job",
        learning_style=LearningStyle.READING, daily_hours=2, target_duration=6,
    )
    db.add(roadmap)
    await db.flush()

    phase = RoadmapPhase(roadmap_id=roadmap.id, order=1, title="P", description="d", duration_weeks=2)
    db.add(phase)
    await db.flush()

    task = RoadmapTask(phase_id=phase.id, title="Task", order=1, completed=False)
    db.add(task)
    await db.flush()

    made = []
    for order, (kind, completed, minutes) in enumerate(units, start=1):
        unit = TaskLearningUnit(
            task_id=task.id, day=order, order=1, type=LearningUnitType(kind),
            title=f"{kind} {order}", estimated_minutes=minutes, completed=completed,
        )
        db.add(unit)
        made.append(unit)

    await db.flush()

    return roadmap, task, made


async def unlocked_codes(db, profile):
    return set(
        (
            await db.execute(
                select(Achievement.code)
                .join(UserAchievement, UserAchievement.achievement_id == Achievement.id)
                .where(UserAchievement.profile_id == profile.id)
            )
        ).scalars()
    )


def test_real_db_the_catalogue_is_copied_and_kept_current():
    async def check(db, me):
        service = AchievementService(db)

        first = await service.ensure_catalog()
        assert [a.code for a in first] == [c[0] for c in ACHIEVEMENTS]

        first[0].xp_reward = 999  # drifted from the file
        await db.flush()

        again = await service.ensure_catalog()
        assert again[0].xp_reward == ACHIEVEMENTS[0][5]  # the file wins
        assert (await db.execute(select(func.count()).select_from(Achievement))).scalar_one() == len(ACHIEVEMENTS)

    with_db(check)


def test_real_db_finishing_lessons_unlocks_badges_pays_xp_once_and_notifies():
    async def check(db, me):
        await make_roadmap(db, me, [("reading", True, 30)])
        service = AchievementService(db)

        unlocked = await service.evaluate(me)
        codes = {a.code for a in unlocked}

        assert "first_lesson" in codes
        assert me.xp == sum(a.xp_reward for a in unlocked)  # bonus XP, once each

        notes = (
            await db.execute(select(Notification).where(Notification.profile_id == me.id, Notification.type == "achievement"))
        ).scalars().all()
        assert {n.dedupe_key for n in notes} == {f"achievement:{c}" for c in codes}
        assert any("First Step" in n.title and "+10 XP" in n.body for n in notes)

        xp_before = me.xp
        assert await service.evaluate(me) == []  # nothing new, nothing paid twice
        assert me.xp == xp_before
        assert await unlocked_codes(db, me) == codes

    with_db(check)


def test_real_db_bonus_xp_can_unlock_a_level_badge_in_the_same_evaluation():
    async def check(db, me):
        me.xp = 395  # level 4; the first-lesson bonus (+10) takes them to level 5
        await make_roadmap(db, me, [("reading", True, 30)])

        codes = {a.code for a in await AchievementService(db).evaluate(me)}

        assert {"first_lesson", "level_5"} <= codes

    with_db(check)


def test_real_db_award_checks_achievements_after_paying_xp():
    async def check(db, me):
        await make_roadmap(db, me, [("reading", True, 30)])
        service = GamificationService(db)

        assert await REAL_AWARD(service, me, 10, "lesson_completed", uuid4()) is True

        assert "first_lesson" in await unlocked_codes(db, me)
        events = (await db.execute(select(XPEvent.reason).where(XPEvent.profile_id == me.id))).scalars().all()
        assert sorted(events) == ["achievement", "lesson_completed"] or "lesson_completed" in events

        # an XP award for something already paid does nothing and checks nothing
        ref = uuid4()
        assert await REAL_AWARD(service, me, 10, "lesson_completed", ref) is True
        assert await REAL_AWARD(service, me, 10, "lesson_completed", ref) is False

    with_db(check)


def test_real_db_a_failing_check_never_breaks_the_action(monkeypatch):
    async def check(db, me):
        async def boom(self, profile):
            raise RuntimeError("badge check broke")

        monkeypatch.setattr(AchievementService, "evaluate", boom)

        assert await AchievementService(db).safe_evaluate(me) == []

        # the session still works afterwards
        assert (await db.execute(select(func.count()).select_from(Profile))).scalar_one() >= 1

    with_db(check)


def test_real_db_listing_shows_progress_and_unlock_times():
    async def check(db, me):
        await make_roadmap(db, me, [("reading", True, 30)] * 1 + [("reading", False, 30)])
        listing = await AchievementService(db).listing(me)

        by_code = {i["code"]: i for i in listing["items"]}

        assert by_code["first_lesson"]["unlocked"] and by_code["first_lesson"]["unlocked_at"]
        assert by_code["lessons_25"]["unlocked"] is False
        assert (by_code["lessons_25"]["current"], by_code["lessons_25"]["target"]) == (1, 25)
        assert listing["unlocked_count"] == sum(1 for i in listing["items"] if i["unlocked"])
        assert listing["total"] == len(ACHIEVEMENTS)

    with_db(check)


def test_real_db_the_monthly_boss():
    async def check(db, me):
        service = AchievementService(db)

        assert await service.boss(me) is None  # no roadmap, no boss

        _, _, units = (await make_roadmap(db, me, [("reading", True, 30), ("project", False, 120)]))[0:3]
        project = units[1]

        boss = await service.boss(me)
        assert boss["title"] == project.title and boss["unit_id"] == project.id
        assert boss["bonus_xp"] == BOSS_BONUS_XP and boss["defeated"] is False
        assert 1 <= boss["days_left"] <= 31

        # the same boss all month, even if another project turns up
        await make_roadmap(db, me, [("project", False, 60)], status=RoadmapStatus.ARCHIVED)
        assert (await service.boss(me))["unit_id"] == project.id

        # finishing it pays the bonus once and unlocks Boss Slayer
        project.completed = True
        await db.flush()
        xp_before = me.xp
        assert await service.sync_boss(me) is True
        assert me.xp - xp_before == BOSS_BONUS_XP
        assert await service.sync_boss(me) is False  # not paid twice

        assert (await service.boss(me))["defeated"] is True
        assert "boss_slayer" in {a.code for a in await service.evaluate(me)}

        notes = (await db.execute(select(Notification.type).where(Notification.profile_id == me.id))).scalars().all()
        assert "boss_defeated" in notes

    with_db(check)


def test_real_db_a_new_month_brings_a_new_boss():
    async def check(db, me):
        service = AchievementService(db)
        _, _, units = await make_roadmap(db, me, [("project", False, 60), ("project", False, 60)])

        first = await service.boss(me)
        row = (await db.execute(select(BossChallenge).where(BossChallenge.profile_id == me.id))).scalar_one()
        row.month = "2020-01"  # pretend that was an old month
        await db.flush()

        second = await service.boss(me)

        assert second is not None
        assert (await db.execute(select(func.count()).select_from(BossChallenge).where(BossChallenge.profile_id == me.id))).scalar_one() == 2
        assert first["unit_id"] == second["unit_id"]  # still the first unfinished project

    with_db(check)


def test_real_db_readiness_is_measured_from_the_database():
    async def check(db, me):
        await make_roadmap(db, me, [("project", True, 60), ("project", False, 60), ("reading", True, 30)])

        stats = await ReadinessService(db).stats(me)

        assert (stats.projects_total, stats.projects_done) == (2, 1)
        assert stats.tasks_total == 1 and stats.tasks_done == 0
        assert stats.interviews_done == 0 and stats.portfolio_public is False
        assert stats.active_days == 0

        db.add(XPEvent(profile_id=me.id, amount=10, reason="lesson_completed", ref_id=uuid4()))
        db.add(XPEvent(profile_id=me.id, amount=50, reason="achievement", ref_id=uuid4()))  # a bonus is not studying
        await db.flush()

        assert (await ReadinessService(db).stats(me)).active_days == 1

        result = await ReadinessService(db).get(me)
        assert 0 <= result["score"] <= 100 and len(result["components"]) == 5

    with_db(check)
