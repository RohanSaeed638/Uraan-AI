"""Read-only numbers for the admin portal: lesson quality, the sign-up funnel, AI spend.
Every route needs an admin, like the rest of /admin."""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.admin import Admin, require_admin
from app.db.base import get_db
from app.services.insights_service import InsightsService

router = APIRouter(prefix="/admin/insights", tags=["Admin insights"])


class ReasonCount(BaseModel):
    reason: str
    count: int


class CareerQuality(BaseModel):
    career_slug: str
    helpful: int
    not_helpful: int
    helpful_percent: float | None = None


class TopicQuality(BaseModel):
    task_title: str
    career_slug: str | None = None
    helpful: int
    not_helpful: int


class FeedbackItem(BaseModel):
    created_at: datetime
    career_slug: str | None = None
    task_title: str | None = None
    lesson_title: str | None = None
    lesson_type: str | None = None
    reason: str | None = None
    comment: str | None = None


class FeedbackOverview(BaseModel):
    days: int
    total: int
    helpful: int
    not_helpful: int
    helpful_percent: float | None = None
    by_reason: list[ReasonCount]
    by_career: list[CareerQuality]
    topics: list[TopicQuality]
    recent: list[FeedbackItem]


@router.get("/feedback", response_model=FeedbackOverview)
async def feedback(
    days: int = Query(default=30, ge=1, le=365),
    admin: Admin = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await InsightsService(db).feedback(days)


class FunnelStep(BaseModel):
    key: str
    count: int
    # A share of everyone who signed up (for "returned": of those who signed up a week or more ago).
    of_signups: float | None = None
    of_previous: float | None = None


class Cohort(BaseModel):
    week: str
    signups: int
    onboarded: int
    roadmap: int
    first_lesson: int
    returned: int
    finished: int
    eligible_for_return: int


class Funnel(BaseModel):
    weeks: int
    eligible_for_return: int
    steps: list[FunnelStep]
    cohorts: list[Cohort]


@router.get("/funnel", response_model=Funnel)
async def funnel(
    weeks: int = Query(default=8, ge=1, le=52),
    admin: Admin = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await InsightsService(db).funnel(weeks)


class ModelUsage(BaseModel):
    provider: str
    model: str
    requests: int
    failed: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float | None = None


class PurposeUsage(BaseModel):
    purpose: str
    requests: int
    failed: int
    tokens: int


class DayUsage(BaseModel):
    date: str
    requests: int
    tokens: int
    estimated_cost_usd: float


class UserUsage(BaseModel):
    profile_id: str
    name: str
    requests: int
    tokens: int


class AiUsage(BaseModel):
    days: int
    requests: int
    failed: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float | None = None
    unpriced_tokens: int
    daily_limit_per_user: int | None = None
    users_over_limit_today: int | None = None
    by_model: list[ModelUsage]
    by_purpose: list[PurposeUsage]
    daily: list[DayUsage]
    top_users: list[UserUsage]


@router.get("/ai-usage", response_model=AiUsage)
async def ai_usage(
    days: int = Query(default=30, ge=1, le=365),
    admin: Admin = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await InsightsService(db).ai_usage(days)


class DeadLink(BaseModel):
    url: str
    http_status: int | None = None
    reason: str | None = None
    fail_count: int
    checked_at: datetime


class LinkOverview(BaseModel):
    ok: int
    dead: int
    unknown: int
    last_checked: datetime | None = None
    dead_links: list[DeadLink]


@router.get("/links", response_model=LinkOverview)
async def links(
    admin: Admin = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await InsightsService(db).links()
