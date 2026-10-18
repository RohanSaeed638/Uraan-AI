from pydantic import BaseModel


class GamificationResponse(BaseModel):
    xp: int
    level: int
    xp_into_level: int
    xp_per_level: int
    streak_days: int
    active_today: bool
    weekly_xp: int
