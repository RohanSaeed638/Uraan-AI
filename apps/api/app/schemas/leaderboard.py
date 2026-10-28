from typing import Literal

from pydantic import BaseModel

LeaderboardPeriod = Literal["weekly", "all_time"]


class LeaderboardEntry(BaseModel):
    rank: int
    display_name: str
    xp: int
    level: int
    is_me: bool = False


class LeaderboardMe(BaseModel):
    xp: int
    rank: int | None = None
    on_leaderboard: bool


class LeaderboardResponse(BaseModel):
    period: LeaderboardPeriod
    entries: list[LeaderboardEntry]
    me: LeaderboardMe
