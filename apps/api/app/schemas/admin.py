import re
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

Level = Literal["beginner", "intermediate", "advanced"]
Demand = Literal["low", "medium", "high", "very_high"]
ResourceType = Literal["course", "video", "docs", "book", "practice"]

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _clean(value: str) -> str:
    return " ".join(value.split())


def _url(value: str) -> str:
    value = value.strip()

    if not re.match(r"^https?://[^\s]+$", value):
        raise ValueError("A link must start with http:// or https://")

    return value


# ---- who is asking ----------------------------------------------------------------------------------------------------------


class AdminMe(BaseModel):
    id: UUID
    name: str
    email: str | None = None


# ---- overview -------------------------------------------------------------------------------------------------------------------


class Counts(BaseModel):
    users: int
    new_users_7d: int
    active_users_7d: int
    roadmaps: int
    lessons_completed: int
    tasks_completed: int
    mentor_messages: int


class AiPurposeStats(BaseModel):
    purpose: str
    requests: int
    failures: int
    failure_rate: float
    avg_latency_ms: int | None = None


class AiProviderStats(BaseModel):
    provider: str
    requests: int
    failures: int


class AiFailure(BaseModel):
    at: datetime
    purpose: str
    provider: str
    error_type: str | None = None


class AdminStats(BaseModel):
    counts: Counts
    days: int
    ai_requests: int
    ai_failures: int
    ai_by_purpose: list[AiPurposeStats]
    ai_by_provider: list[AiProviderStats]
    recent_failures: list[AiFailure]


# ---- users ---------------------------------------------------------------------------------------------------------------------------


class AdminUser(BaseModel):
    id: UUID
    name: str
    email: str | None = None
    role: str
    language: str
    career_slug: str | None = None
    xp: int
    streak_days: int
    roadmaps: int
    created_at: datetime
    last_activity_date: str | None = None


class AdminUserList(BaseModel):
    items: list[AdminUser]
    total: int


class RoleRequest(BaseModel):
    role: Literal["user", "admin"]

    model_config = ConfigDict(extra="forbid")


# ---- careers -------------------------------------------------------------------------------------------------------------------------


class CareerSkillIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def tidy(cls, value):
        return _clean(value)


class CareerResourceIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    type: ResourceType
    provider: str | None = Field(default=None, max_length=120)
    url: str = Field(max_length=500)
    is_free: bool = True
    difficulty: Level | None = None

    @field_validator("url")
    @classmethod
    def check_url(cls, value):
        return _url(value)

    @field_validator("title", "provider")
    @classmethod
    def tidy(cls, value):
        return _clean(value) if value else value


class CareerFields(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    category: str | None = Field(default=None, max_length=60)
    icon: str | None = Field(default=None, max_length=40)
    color: str | None = None
    difficulty: Level | None = None
    estimated_months: int | None = Field(default=None, ge=1, le=60)
    salary_min_pkr: int | None = Field(default=None, ge=0, le=100_000_000)
    salary_max_pkr: int | None = Field(default=None, ge=0, le=100_000_000)
    market_demand: Demand | None = None
    is_active: bool = True
    skills: list[CareerSkillIn] = Field(default_factory=list, max_length=40)
    resources: list[CareerResourceIn] = Field(default_factory=list, max_length=40)

    @field_validator("name", "category")
    @classmethod
    def tidy(cls, value):
        return _clean(value) if value else value

    @field_validator("color")
    @classmethod
    def hex_colour(cls, value):
        if value and not re.match(r"^#[0-9a-fA-F]{6}$", value):
            raise ValueError("Use a colour like #7C3AED")

        return value or None

    def check_salary(self):
        if self.salary_min_pkr and self.salary_max_pkr and self.salary_min_pkr > self.salary_max_pkr:
            raise ValueError("The lowest salary cannot be above the highest")


class CareerCreate(CareerFields):
    slug: str = Field(min_length=2, max_length=60)

    @field_validator("slug")
    @classmethod
    def slug_format(cls, value):
        value = value.strip().lower()

        if not SLUG.match(value):
            raise ValueError("Use lowercase words joined by hyphens, like data-analyst")

        return value


class CareerUpdate(CareerFields):
    """Everything but the slug, which roadmaps and profiles point to."""


class AdminCareer(CareerFields):
    id: UUID
    slug: str

    model_config = ConfigDict(from_attributes=True)


class AdminCareerRow(BaseModel):
    id: UUID
    slug: str
    name: str
    category: str | None = None
    difficulty: str | None = None
    market_demand: str | None = None
    is_active: bool
    skills: int
    resources: int


# ---- library resources -------------------------------------------------------------------------------------------


class ResourceFields(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    url: str = Field(max_length=500)
    type: ResourceType
    provider: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    is_free: bool = True
    difficulty: Level | None = None
    career_slugs: list[str] = Field(default_factory=list, max_length=30)
    language: Literal["en", "ur", "ur-Latn"] = "en"
    is_active: bool = True

    @field_validator("url")
    @classmethod
    def check_url(cls, value):
        return _url(value)

    @field_validator("title", "provider", "description")
    @classmethod
    def tidy(cls, value):
        return _clean(value) if value else value


class AdminResource(ResourceFields):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class AdminResourceList(BaseModel):
    items: list[AdminResource]
    total: int


# ---- announcements ------------------------------------------------------------------------------------------------------


class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    body: str = Field(min_length=2, max_length=2000)
    level: Literal["info", "warning"] = "info"
    ends_at: datetime | None = None
    # Also send everyone a notification now.
    notify: bool = False

    @field_validator("title", "body")
    @classmethod
    def tidy(cls, value):
        return value.strip()


class AnnouncementUpdate(BaseModel):
    is_active: bool | None = None
    ends_at: datetime | None = None

    model_config = ConfigDict(extra="forbid")


class AnnouncementOut(BaseModel):
    id: UUID
    title: str
    body: str
    level: str
    is_active: bool
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    notified: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActiveAnnouncement(BaseModel):
    id: UUID
    title: str
    body: str
    level: str

    model_config = ConfigDict(from_attributes=True)


# ---- audit ----------------------------------------------------------------------------------------------------------------------------


class AuditEntry(BaseModel):
    id: UUID
    at: datetime
    actor: str
    action: str
    target_type: str
    target_id: str | None = None
    summary: str
    changes: dict | None = None


class AuditList(BaseModel):
    items: list[AuditEntry]
    has_more: bool = False
