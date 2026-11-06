from pydantic import BaseModel


class GamificationResponse(BaseModel):
    xp: int
    career_title: str
    next_career_title: str | None = None
    xp_to_next_title: int | None = None
    title_progress: float = 0
    level: int
    xp_into_level: int
    xp_per_level: int
    streak_days: int
    streak_freezes: int = 0
    # True while the streak is only alive because freezes will cover the missed days.
    streak_protected: bool = False
    active_today: bool
    weekly_xp: int
