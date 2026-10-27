"""Gathers the numbers for the career readiness score (see readiness.py)."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
from app.services.readiness import WINDOW_DAYS, ReadinessStats, compute_readiness

# Progress is measured on the roadmap the learner is working through: the
# active one, else the newest that is not archived.
ROADMAP_SQL = text(
    """
    select id from roadmaps
     where profile_id = :p and status::text in ('active', 'paused', 'completed')
     order by (status::text = 'active') desc, created_at desc
     limit 1
    """
)

PROGRESS_SQL = text(
    """
    select
      count(*) filter (where true) as tasks_total,
      count(*) filter (where t.completed) as tasks_done
    from roadmap_tasks t
      join roadmap_phases p on p.id = t.phase_id
     where p.roadmap_id = :r
    """
)

PROJECTS_SQL = text(
    """
    select
      count(*) as projects_total,
      count(*) filter (where u.completed) as projects_done
    from task_learning_units u
      join roadmap_tasks t on t.id = u.task_id
      join roadmap_phases p on p.id = t.phase_id
     where p.roadmap_id = :r and u.type::text = 'project'
    """
)

ACTIVE_DAYS_SQL = text(
    """
    select count(distinct (created_at at time zone :tz)::date)
      from xp_events
     where profile_id = :p
       and created_at >= now() - make_interval(days => :days)
       and reason <> 'achievement'
    """
)

INTERVIEWS_SQL = text(
    """
    select count(*) as done,
           coalesce((select avg(overall_score) from (
              select overall_score from interview_sessions
               where profile_id = :p and status = 'completed' and overall_score is not null
               order by created_at desc limit 3) latest), 0) as avg_score
      from interview_sessions
     where profile_id = :p and status = 'completed'
    """
)

PORTFOLIO_SQL = text(
    """
    select coalesce(bool_or(po.is_public), false) as is_public,
           coalesce(bool_or(coalesce(po.headline, '') <> '' and coalesce(po.bio, '') <> ''), false) as has_intro,
           (select count(*) from portfolio_projects pp
             where pp.profile_id = :p and pp.visible) as projects
      from portfolios po
     where po.profile_id = :p
    """
)


def valid_timezone(name: str | None) -> str:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    try:
        ZoneInfo(name or "UTC")
    except (ZoneInfoNotFoundError, ValueError):
        return "UTC"

    return name or "UTC"


class ReadinessService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def stats(self, profile: Profile) -> ReadinessStats:
        p = {"p": profile.id}
        stats = ReadinessStats()

        roadmap_id = (await self.db.execute(ROADMAP_SQL, p)).scalar_one_or_none()

        if roadmap_id is not None:
            progress = (await self.db.execute(PROGRESS_SQL, {"r": roadmap_id})).one()
            projects = (await self.db.execute(PROJECTS_SQL, {"r": roadmap_id})).one()
            stats.tasks_total, stats.tasks_done = progress.tasks_total, progress.tasks_done
            stats.projects_total, stats.projects_done = projects.projects_total, projects.projects_done

        stats.active_days = (
            await self.db.execute(
                ACTIVE_DAYS_SQL,
                {"p": profile.id, "tz": valid_timezone(profile.timezone), "days": WINDOW_DAYS},
            )
        ).scalar_one()

        interviews = (await self.db.execute(INTERVIEWS_SQL, p)).one()
        stats.interviews_done = interviews.done
        stats.interview_avg_score = float(interviews.avg_score or 0)

        portfolio = (await self.db.execute(PORTFOLIO_SQL, p)).one()
        stats.portfolio_public = bool(portfolio.is_public)
        stats.portfolio_intro = bool(portfolio.has_intro)
        stats.portfolio_projects = portfolio.projects

        return stats

    async def get(self, profile: Profile) -> dict:
        return compute_readiness(await self.stats(profile))
