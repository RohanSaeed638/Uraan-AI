"""Achievements and the monthly boss project.

`evaluate` is cheap and idempotent: it is called after XP is awarded and
whenever something else that can earn a badge changes (publishing a portfolio,
creating a document, asking the mentor). A badge unlocks once, pays its XP
once and sends one notification."""
import logging
from calendar import monthrange
from datetime import date, datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.achievement_catalog import ACHIEVEMENTS, BOSS_BONUS_XP
from app.core.texts import text as message
from app.models.achievement import Achievement, BossChallenge, UserAchievement
from app.models.profile import Profile
from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.models.task_learning_unit import TaskLearningUnit
from app.repositories.notification_repository import NotificationRepository
from app.services.email_service import EmailService
from app.services.gamification_service import GamificationService, level_for, local_today

logger = logging.getLogger(__name__)

REASON_ACHIEVEMENT = "achievement"
REASON_BOSS = "boss_project"

TYPE_ACHIEVEMENT = "achievement"
TYPE_BOSS = "boss_defeated"
TYPE_STREAK = "streak"

# Streak lengths worth a celebration (in the app and by email).
STREAK_MILESTONES = {3, 7, 14, 30, 60, 100, 200, 365}

# Unlocking pays XP, which can unlock a level badge: go round until stable.
MAX_ROUNDS = 3

STATS_SQL = text(
    """
    select
      (select count(*) from task_learning_units u
         join roadmap_tasks t on t.id = u.task_id
         join roadmap_phases p on p.id = t.phase_id
         join roadmaps r on r.id = p.roadmap_id
        where r.profile_id = :p and u.completed) as lessons,
      (select count(*) from task_learning_units u
         join roadmap_tasks t on t.id = u.task_id
         join roadmap_phases p on p.id = t.phase_id
         join roadmaps r on r.id = p.roadmap_id
        where r.profile_id = :p and u.completed and u.type::text = 'project') as projects,
      (select coalesce(sum(u.estimated_minutes), 0) from task_learning_units u
         join roadmap_tasks t on t.id = u.task_id
         join roadmap_phases p on p.id = t.phase_id
         join roadmaps r on r.id = p.roadmap_id
        where r.profile_id = :p and u.completed) as minutes,
      (select count(*) from roadmap_tasks t
         join roadmap_phases p on p.id = t.phase_id
         join roadmaps r on r.id = p.roadmap_id
        where r.profile_id = :p and t.completed) as tasks,
      (select count(distinct a.task_id) from quiz_attempts a
        where a.profile_id = :p and a.passed) as quizzes_passed,
      (select count(*) from interview_sessions i
        where i.profile_id = :p and i.status = 'completed') as interviews,
      (select count(*) from documents d where d.profile_id = :p) as documents,
      (select count(*) from mentor_messages m
         join mentor_conversations c on c.id = m.conversation_id
        where c.profile_id = :p and m.role = 'user') as mentor_chats,
      (select count(*) from roadmaps r
        where r.profile_id = :p and r.status::text = 'completed') as roadmaps_completed,
      (select count(*) from portfolios po
        where po.profile_id = :p and po.is_public) as portfolio_public,
      (select count(*) from boss_challenges b
        where b.profile_id = :p and b.completed_at is not null) as bosses
    """
)


def days_left_in_month(today: date) -> int:
    """Days from today to the last day of the month, today included."""
    return monthrange(today.year, today.month)[1] - today.day + 1


def measures(row: dict, profile) -> dict[str, float]:
    """The learner stats the achievement rules read."""
    return {
        "lessons": row["lessons"],
        "tasks": row["tasks"],
        "projects": row["projects"],
        "hours": (row["minutes"] or 0) / 60,
        "quizzes_passed": row["quizzes_passed"],
        "interviews": row["interviews"],
        "documents": row["documents"],
        "mentor_chats": row["mentor_chats"],
        "roadmaps_completed": row["roadmaps_completed"],
        "portfolio_public": min(row["portfolio_public"], 1),
        "bosses": row["bosses"],
        "streak": profile.streak_days or 0,
        "level": level_for(profile.xp or 0),
    }


def unlocked_by(stats: dict[str, float], catalog: list, already: set[str]) -> list:
    """The achievements `stats` earn that are not unlocked yet."""
    return [
        a
        for a in catalog
        if a.is_active and a.code not in already and stats.get(a.rule, 0) >= a.threshold
    ]


class AchievementService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notifications = NotificationRepository(db)

    # ---- the catalogue -----------------------------------------------------------------------

    async def ensure_catalog(self) -> list[Achievement]:
        """Copies the catalogue file into the table (inserting new badges and
        updating changed ones), and returns every badge."""
        rows = {a.code: a for a in (await self.db.execute(select(Achievement))).scalars()}
        changed = False

        for position, (code, title, desc, category, icon, xp, rule, threshold) in enumerate(ACHIEVEMENTS):
            row = rows.get(code)

            if row is None:
                row = Achievement(code=code)
                self.db.add(row)
                rows[code] = row
                changed = True

            wanted = dict(
                title=title, description=desc, category=category, icon=icon,
                xp_reward=xp, rule=rule, threshold=threshold, position=position,
            )

            for field, value in wanted.items():
                if getattr(row, field, None) != value:
                    setattr(row, field, value)
                    changed = True

        if changed:
            await self.db.flush()

        return sorted(rows.values(), key=lambda a: a.position)

    # ---- what the learner has done ---------------------------------------------------------------

    async def stats(self, profile: Profile) -> dict[str, float]:
        row = (await self.db.execute(STATS_SQL, {"p": profile.id})).mappings().one()

        return measures(dict(row), profile)

    # ---- unlocking ------------------------------------------------------------------------------------

    async def evaluate(self, profile: Profile) -> list[Achievement]:
        """Unlocks what the learner has earned. Returns the new unlocks."""
        catalog = await self.ensure_catalog()
        already = set(
            (
                await self.db.execute(
                    select(Achievement.code)
                    .join(UserAchievement, UserAchievement.achievement_id == Achievement.id)
                    .where(UserAchievement.profile_id == profile.id)
                )
            ).scalars()
        )

        gamification = GamificationService(self.db)
        unlocked: list[Achievement] = []

        for _ in range(MAX_ROUNDS):
            await self.sync_boss(profile)
            earned = unlocked_by(await self.stats(profile), catalog, already)

            if not earned:
                break

            for achievement in earned:
                inserted = (
                    await self.db.execute(
                        insert(UserAchievement)
                        .values(profile_id=profile.id, achievement_id=achievement.id)
                        .on_conflict_do_nothing(index_elements=["profile_id", "achievement_id"])
                        .returning(UserAchievement.id)
                    )
                ).scalar_one_or_none()

                already.add(achievement.code)

                if inserted is None:
                    continue  # unlocked by a request running at the same time

                unlocked.append(achievement)

                # The bonus never starts another evaluation: this loop does.
                await gamification.award(
                    profile, achievement.xp_reward, REASON_ACHIEVEMENT, achievement.id,
                    evaluate=False,
                )
                await self._notify(
                    profile,
                    TYPE_ACHIEVEMENT,
                    message("achievement_title", profile.language, title=achievement.title),
                    message(
                        "achievement_body", profile.language,
                        description=achievement.description, xp=achievement.xp_reward,
                    ),
                    f"achievement:{achievement.code}",
                )

        await self._streak_milestone(profile)

        return unlocked

    async def _notify(self, profile: Profile, type: str, title: str, body: str, dedupe_key: str) -> None:
        """The in-app notification, and the email for it the first time."""
        created = await self.notifications.create_once(
            profile_id=profile.id,
            type=type,
            title=title,
            body=body,
            url="/achievements",
            dedupe_key=dedupe_key,
        )

        if created is not None:
            await EmailService(self.db).notify(profile, type, title, body, "/achievements")

    async def _streak_milestone(self, profile: Profile) -> None:
        days = profile.streak_days or 0

        if days in STREAK_MILESTONES:
            await self._notify(
                profile,
                TYPE_STREAK,
                message("streak_title", profile.language, days=days),
                message("streak_body", profile.language, days=days),
                f"streak:{days}:{local_today(profile.timezone).isoformat()}",
            )

    async def safe_evaluate(self, profile: Profile) -> list[Achievement]:
        """`evaluate` for the places that must not fail because of it: the
        learner's own action (finishing a lesson, publishing a portfolio...)
        still succeeds if badges cannot be checked. Pending changes are
        flushed first so the check sees them; a failure undoes only itself."""
        try:
            await self.db.flush()

            async with self.db.begin_nested():
                return await self.evaluate(profile)
        except Exception:
            logger.exception("Achievement check failed")

            return []

    # ---- listing ---------------------------------------------------------------------------------------------

    async def listing(self, profile: Profile) -> dict:
        await self.evaluate(profile)
        catalog = await self.ensure_catalog()
        stats = await self.stats(profile)

        unlocked_at = {
            code: when
            for code, when in (
                await self.db.execute(
                    select(Achievement.code, UserAchievement.unlocked_at)
                    .join(UserAchievement, UserAchievement.achievement_id == Achievement.id)
                    .where(UserAchievement.profile_id == profile.id)
                )
            ).all()
        }

        items = [
            {
                "code": a.code,
                "title": a.title,
                "description": a.description,
                "category": a.category,
                "icon": a.icon,
                "xp_reward": a.xp_reward,
                "unlocked": a.code in unlocked_at,
                "unlocked_at": unlocked_at.get(a.code),
                "current": min(round(stats.get(a.rule, 0), 1), a.threshold),
                "target": a.threshold,
            }
            for a in catalog
            if a.is_active
        ]

        return {
            "items": items,
            "unlocked_count": sum(1 for i in items if i["unlocked"]),
            "total": len(items),
            "boss": await self.boss(profile),
        }

    # ---- the monthly boss -----------------------------------------------------------------------------------------

    @staticmethod
    def month_key(profile: Profile) -> str:
        return local_today(profile.timezone).strftime("%Y-%m")

    async def _boss_row(self, profile: Profile) -> BossChallenge | None:
        return (
            await self.db.execute(
                select(BossChallenge).where(
                    BossChallenge.profile_id == profile.id,
                    BossChallenge.month == self.month_key(profile),
                )
            )
        ).scalar_one_or_none()

    async def _pick_boss_unit(self, profile: Profile) -> TaskLearningUnit | None:
        """The first unfinished project lesson of the active roadmap."""
        return (
            await self.db.execute(
                select(TaskLearningUnit)
                .join(RoadmapTask, RoadmapTask.id == TaskLearningUnit.task_id)
                .join(RoadmapPhase, RoadmapPhase.id == RoadmapTask.phase_id)
                .join(Roadmap, Roadmap.id == RoadmapPhase.roadmap_id)
                .where(
                    Roadmap.profile_id == profile.id,
                    Roadmap.status == "active",
                    TaskLearningUnit.type == "project",
                    TaskLearningUnit.completed.is_(False),
                )
                .order_by(RoadmapPhase.order, RoadmapTask.order, TaskLearningUnit.day)
                .limit(1)
            )
        ).scalar_one_or_none()

    async def boss(self, profile: Profile) -> dict | None:
        """This month's boss project, choosing one on first request."""
        row = await self._boss_row(profile)

        if row is None:
            unit = await self._pick_boss_unit(profile)

            if unit is None:
                return None

            await self.db.execute(
                insert(BossChallenge)
                .values(
                    profile_id=profile.id,
                    month=self.month_key(profile),
                    unit_id=unit.id,
                    bonus_xp=BOSS_BONUS_XP,
                )
                .on_conflict_do_nothing(index_elements=["profile_id", "month"])
            )
            row = await self._boss_row(profile)

        info = (
            await self.db.execute(
                select(TaskLearningUnit, RoadmapTask, Roadmap)
                .join(RoadmapTask, RoadmapTask.id == TaskLearningUnit.task_id)
                .join(RoadmapPhase, RoadmapPhase.id == RoadmapTask.phase_id)
                .join(Roadmap, Roadmap.id == RoadmapPhase.roadmap_id)
                .where(TaskLearningUnit.id == row.unit_id)
            )
        ).first()

        if info is None:
            return None

        unit, task, roadmap = info
        today = local_today(profile.timezone)

        return {
            "unit_id": unit.id,
            "title": unit.title,
            "task_title": task.title,
            "roadmap_id": roadmap.id,
            "task_id": task.id,
            "bonus_xp": row.bonus_xp,
            "defeated": row.completed_at is not None,
            "days_left": days_left_in_month(today),
        }

    async def sync_boss(self, profile: Profile) -> bool:
        """Pays the bonus when this month's boss project has been finished.
        Returns whether it was defeated just now."""
        row = await self._boss_row(profile)

        if row is None or row.completed_at is not None:
            return False

        done = (
            await self.db.execute(
                select(TaskLearningUnit.completed).where(TaskLearningUnit.id == row.unit_id)
            )
        ).scalar_one_or_none()

        if not done:
            return False

        row.completed_at = datetime.now(timezone.utc)
        await GamificationService(self.db).award(
            profile, row.bonus_xp, REASON_BOSS, row.unit_id, evaluate=False
        )
        await self._notify(
            profile,
            TYPE_BOSS,
            message("boss_title", profile.language),
            message("boss_body", profile.language, xp=row.bonus_xp),
            f"boss:{row.month}",
        )
        await self.db.flush()

        return True
