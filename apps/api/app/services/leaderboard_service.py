from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.leaderboard_repository import LeaderboardRepository
from app.repositories.profile_repository import ProfileRepository
from app.schemas.leaderboard import (
    LeaderboardEntry,
    LeaderboardMe,
    LeaderboardPeriod,
    LeaderboardResponse,
)
from app.services.gamification_service import level_for

TOP_N = 50


def display_name(full_name: str | None) -> str:
    """First name plus last initial, so full names are never shown."""
    parts = (full_name or "").split()

    if not parts:
        return "Learner"

    if len(parts) == 1:
        return parts[0]

    return f"{parts[0]} {parts[-1][0].upper()}."


def week_start(now: datetime | None = None) -> datetime:
    """Monday 00:00 UTC of the current week."""
    now = now or datetime.now(timezone.utc)
    monday = now - timedelta(days=now.weekday())

    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


class LeaderboardService:

    def __init__(self, db: AsyncSession):
        self.profile_repository = ProfileRepository(db)
        self.repository = LeaderboardRepository(db)

    async def get(
        self,
        period: LeaderboardPeriod,
        auth_user_id: UUID,
    ) -> LeaderboardResponse:
        profile = await self.profile_repository.get_by_auth_user_id(
            auth_user_id
        )

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        since = week_start() if period == "weekly" else None

        rows = await self.repository.top(since, TOP_N)

        entries = [
            LeaderboardEntry(
                rank=index,
                display_name=display_name(row.full_name),
                xp=int(row.score),
                level=level_for(int(row.xp or 0)),
                is_me=row.id == profile.id,
            )
            for index, row in enumerate(rows, start=1)
        ]

        opted_in = await self.repository.is_opted_in(profile.id)
        my_score = await self.repository.score_of(profile.id, since)

        # A rank is only returned when the caller is on the board.
        my_rank = None
        if opted_in and my_score > 0:
            my_rank = await self.repository.rank_of(my_score, since)

        return LeaderboardResponse(
            period=period,
            entries=entries,
            me=LeaderboardMe(
                xp=my_score,
                rank=my_rank,
                on_leaderboard=opted_in,
            ),
        )
