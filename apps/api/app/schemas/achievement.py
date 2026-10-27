from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AchievementItem(BaseModel):
    code: str
    title: str
    description: str
    category: str
    icon: str
    xp_reward: int
    unlocked: bool
    unlocked_at: datetime | None = None
    current: float
    target: int


class BossResponse(BaseModel):
    unit_id: UUID
    title: str
    task_title: str
    roadmap_id: UUID
    task_id: UUID
    bonus_xp: int
    defeated: bool
    days_left: int


class AchievementsResponse(BaseModel):
    items: list[AchievementItem]
    unlocked_count: int
    total: int
    boss: BossResponse | None = None


class ReadinessComponent(BaseModel):
    key: str
    weight: int
    value: float
    points: float


class ReadinessTip(BaseModel):
    key: str
    action: str
    count: int
    href: str


class ReadinessResponse(BaseModel):
    score: int
    level: str
    components: list[ReadinessComponent]
    tips: list[ReadinessTip]
