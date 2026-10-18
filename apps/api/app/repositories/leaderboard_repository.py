from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
from app.models.user_settings import UserSettings
from app.models.xp_event import XPEvent


class LeaderboardRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    def _scores(self, since: datetime | None):
        """One row per profile with its score for the period."""
        if since is None:
            return select(
                Profile.id.label("profile_id"),
                Profile.xp.label("score"),
            ).subquery()

        return (
            select(
                XPEvent.profile_id.label("profile_id"),
                func.sum(XPEvent.amount).label("score"),
            )
            .where(XPEvent.created_at >= since)
            .group_by(XPEvent.profile_id)
            .subquery()
        )

    async def top(
        self,
        since: datetime | None,
        limit: int,
    ):
        """Top opted-in profiles: (id, full_name, score, all-time xp)."""
        scores = self._scores(since)

        stmt = (
            select(
                Profile.id,
                Profile.full_name,
                scores.c.score,
                Profile.xp,
            )
            .join(scores, scores.c.profile_id == Profile.id)
            .join(UserSettings, UserSettings.profile_id == Profile.id)
            .where(
                UserSettings.show_on_leaderboard.is_(True),
                scores.c.score > 0,
            )
            .order_by(scores.c.score.desc(), Profile.created_at.asc())
            .limit(limit)
        )

        return (await self.db.execute(stmt)).all()

    async def score_of(
        self,
        profile_id: UUID,
        since: datetime | None,
    ) -> int:
        scores = self._scores(since)

        result = await self.db.execute(
            select(scores.c.score).where(scores.c.profile_id == profile_id)
        )

        return int(result.scalar_one_or_none() or 0)

    async def rank_of(
        self,
        score: int,
        since: datetime | None,
    ) -> int:
        """Rank among opted-in profiles: 1 + how many score higher."""
        scores = self._scores(since)

        result = await self.db.execute(
            select(func.count())
            .select_from(scores)
            .join(
                UserSettings,
                UserSettings.profile_id == scores.c.profile_id,
            )
            .where(
                UserSettings.show_on_leaderboard.is_(True),
                scores.c.score > score,
            )
        )

        return int(result.scalar_one()) + 1

    async def is_opted_in(self, profile_id: UUID) -> bool:
        result = await self.db.execute(
            select(UserSettings.show_on_leaderboard).where(
                UserSettings.profile_id == profile_id
            )
        )

        return bool(result.scalar_one_or_none())
