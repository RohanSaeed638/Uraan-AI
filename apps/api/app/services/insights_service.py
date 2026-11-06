"""Numbers for the admin: is the content good, are people getting through the product.

Everything here is read-only and computed from the database, so it works without
any analytics provider."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.pricing import estimate_cost
from app.core.config import settings
from app.models.ai_request import AiRequest
from app.models.feedback import LessonFeedback
from app.models.link_check import LinkCheck
from app.models.profile import Profile


def percent(part: int, whole: int) -> float | None:
    """A share as a percentage with one decimal, or None when there is nothing to divide by."""
    if not whole:
        return None

    return round(part * 100 / whole, 1)


class InsightsService:

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---- lesson quality ---------------------------------------------------------------------------------------

    async def feedback(self, days: int = 30) -> dict:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        recent_window = LessonFeedback.created_at >= since
        helpful = func.count().filter(LessonFeedback.helpful.is_(True))
        unhelpful = func.count().filter(LessonFeedback.helpful.is_(False))

        total_row = (
            await self.db.execute(select(helpful, unhelpful).where(recent_window))
        ).one()
        good, bad = int(total_row[0]), int(total_row[1])

        reasons = (
            await self.db.execute(
                select(LessonFeedback.reason, func.count())
                .where(recent_window, LessonFeedback.helpful.is_(False), LessonFeedback.reason.is_not(None))
                .group_by(LessonFeedback.reason)
                .order_by(func.count().desc())
            )
        ).all()

        careers = (
            await self.db.execute(
                select(LessonFeedback.career_slug, helpful, unhelpful)
                .where(recent_window, LessonFeedback.career_slug.is_not(None))
                .group_by(LessonFeedback.career_slug)
                .order_by(unhelpful.desc(), helpful.desc())
                .limit(20)
            )
        ).all()

        # Topics are lessons with the same task title: each learner has their own copy of a lesson,
        # so the same topic being voted down by several people is the signal worth acting on.
        topic = func.lower(LessonFeedback.task_title)
        topics = (
            await self.db.execute(
                select(func.min(LessonFeedback.task_title), LessonFeedback.career_slug, helpful, unhelpful)
                .where(recent_window, LessonFeedback.task_title.is_not(None))
                .group_by(topic, LessonFeedback.career_slug)
                .having(unhelpful > 0)
                .order_by(unhelpful.desc(), helpful.asc())
                .limit(15)
            )
        ).all()

        latest = (
            await self.db.execute(
                select(LessonFeedback)
                .where(recent_window, LessonFeedback.helpful.is_(False))
                .order_by(LessonFeedback.created_at.desc())
                .limit(20)
            )
        ).scalars().all()

        return {
            "days": days,
            "total": good + bad,
            "helpful": good,
            "not_helpful": bad,
            "helpful_percent": percent(good, good + bad),
            "by_reason": [{"reason": reason, "count": int(count)} for reason, count in reasons],
            "by_career": [
                {
                    "career_slug": slug,
                    "helpful": int(g),
                    "not_helpful": int(b),
                    "helpful_percent": percent(int(g), int(g) + int(b)),
                }
                for slug, g, b in careers
            ],
            "topics": [
                {
                    "task_title": title,
                    "career_slug": slug,
                    "helpful": int(g),
                    "not_helpful": int(b),
                }
                for title, slug, g, b in topics
            ],
            "recent": [
                {
                    "created_at": row.created_at,
                    "career_slug": row.career_slug,
                    "task_title": row.task_title,
                    "lesson_title": row.lesson_title,
                    "lesson_type": row.lesson_type,
                    "reason": row.reason,
                    "comment": row.comment,
                }
                for row in latest
            ],
        }

    # ---- the funnel -------------------------------------------------------------------------------------------

    async def funnel(self, weeks: int = 8) -> dict:
        """How far new learners get, by the week they signed up. Staff accounts are left out.

        A learner "returned" if they finished learning something at least a week after signing up; only
        people who signed up more than a week ago can have, so that share is measured against them."""
        rows = (
            await self.db.execute(
                text(
                    """
                    select date_trunc('week', p.created_at) as week,
                           count(*) as signups,
                           count(*) filter (where p.onboarding_completed) as onboarded,
                           count(*) filter (where exists (
                               select 1 from roadmaps r where r.profile_id = p.id and r.status <> 'failed'
                           )) as roadmap,
                           count(*) filter (where exists (
                               select 1 from learning_activities a where a.profile_id = p.id
                           )) as first_lesson,
                           count(*) filter (where p.created_at <= now() - interval '7 days') as eligible,
                           count(*) filter (where p.created_at <= now() - interval '7 days' and exists (
                               select 1 from learning_activities a
                               where a.profile_id = p.id and a.created_at >= p.created_at + interval '7 days'
                           )) as returned,
                           count(*) filter (where exists (
                               select 1 from roadmaps r where r.profile_id = p.id and r.status = 'completed'
                           )) as finished
                    from profiles p
                    where p.role <> 'admin'
                      and p.created_at >= date_trunc('week', now()) - make_interval(weeks => :weeks)
                    group by 1
                    order by 1
                    """
                ),
                {"weeks": weeks - 1},
            )
        ).all()

        keys = ("signups", "onboarded", "roadmap", "first_lesson", "returned", "finished")
        cohorts = [
            {
                "week": row.week.date().isoformat(),
                **{key: int(getattr(row, key)) for key in keys},
                "eligible_for_return": int(row.eligible),
            }
            for row in rows
        ]
        totals = {key: sum(c[key] for c in cohorts) for key in keys}
        eligible = sum(c["eligible_for_return"] for c in cohorts)

        steps, previous = [], None
        for key in ("signups", "onboarded", "roadmap", "first_lesson"):
            steps.append(
                {
                    "key": key,
                    "count": totals[key],
                    "of_signups": percent(totals[key], totals["signups"]),
                    "of_previous": percent(totals[key], previous) if previous is not None else None,
                }
            )
            previous = totals[key]

        steps.append(
            {
                "key": "returned",
                "count": totals["returned"],
                "of_signups": percent(totals["returned"], eligible),
                "of_previous": None,
            }
        )
        steps.append(
            {
                "key": "finished",
                "count": totals["finished"],
                "of_signups": percent(totals["finished"], totals["signups"]),
                "of_previous": None,
            }
        )

        # How long a learner takes to reach their first win: sign-up to first finished lesson, the middle value.
        minutes = (
            await self.db.execute(
                text(
                    """
                    select percentile_cont(0.5) within group (order by extract(epoch from first.at - p.created_at) / 60)
                    from profiles p
                    join lateral (
                        select min(a.created_at) as at from learning_activities a where a.profile_id = p.id
                    ) first on first.at is not null
                    where p.role <> 'admin'
                      and p.created_at >= date_trunc('week', now()) - make_interval(weeks => :weeks)
                    """
                ),
                {"weeks": weeks - 1},
            )
        ).scalar()

        return {
            "weeks": weeks,
            "eligible_for_return": eligible,
            "median_minutes_to_first_lesson": round(float(minutes), 1) if minutes is not None else None,
            "steps": steps,
            "cohorts": cohorts,
        }

    # ---- AI usage and spend -----------------------------------------------------------------------------------

    async def ai_usage(self, days: int = 30) -> dict:
        """Calls, tokens and ESTIMATED cost of the AI features (see app/ai/pricing.py), plus who uses the most."""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        day = func.date(func.timezone("UTC", AiRequest.created_at))
        tokens_in = func.coalesce(func.sum(AiRequest.input_tokens), 0)
        tokens_out = func.coalesce(func.sum(AiRequest.output_tokens), 0)
        failed = func.count().filter(AiRequest.success.is_(False))

        grouped = (
            await self.db.execute(
                select(day, AiRequest.provider, AiRequest.model, func.count(), failed, tokens_in, tokens_out)
                .where(AiRequest.created_at >= since)
                .group_by(day, AiRequest.provider, AiRequest.model)
            )
        ).all()

        by_model: dict[tuple[str, str], dict] = {}
        by_day: dict[str, dict] = {}

        for date, provider, model, calls, fails, t_in, t_out in grouped:
            cost = estimate_cost(model, int(t_in), int(t_out))
            entry = by_model.setdefault(
                (provider, model),
                {"provider": provider, "model": model, "requests": 0, "failed": 0, "input_tokens": 0,
                 "output_tokens": 0, "estimated_cost_usd": 0.0 if cost is not None else None},
            )
            entry["requests"] += int(calls)
            entry["failed"] += int(fails)
            entry["input_tokens"] += int(t_in)
            entry["output_tokens"] += int(t_out)

            if cost is not None:
                entry["estimated_cost_usd"] = (entry["estimated_cost_usd"] or 0.0) + cost

            row = by_day.setdefault(date.isoformat(), {"date": date.isoformat(), "requests": 0, "tokens": 0, "estimated_cost_usd": 0.0})
            row["requests"] += int(calls)
            row["tokens"] += int(t_in) + int(t_out)
            row["estimated_cost_usd"] += cost or 0.0

        purposes = (
            await self.db.execute(
                select(AiRequest.purpose, func.count(), failed, tokens_in + tokens_out)
                .where(AiRequest.created_at >= since)
                .group_by(AiRequest.purpose)
                .order_by((tokens_in + tokens_out).desc())
            )
        ).all()

        users = (
            await self.db.execute(
                select(AiRequest.profile_id, Profile.full_name, func.count(), tokens_in + tokens_out)
                .join(Profile, Profile.id == AiRequest.profile_id, isouter=True)
                .where(AiRequest.created_at >= since, AiRequest.profile_id.is_not(None))
                .group_by(AiRequest.profile_id, Profile.full_name)
                .order_by((tokens_in + tokens_out).desc())
                .limit(10)
            )
        ).all()

        models = sorted(by_model.values(), key=lambda m: -(m["input_tokens"] + m["output_tokens"]))
        priced = [m["estimated_cost_usd"] for m in models if m["estimated_cost_usd"] is not None]
        unpriced_tokens = sum(m["input_tokens"] + m["output_tokens"] for m in models if m["estimated_cost_usd"] is None)

        over_limit = None

        if settings.AI_DAILY_TOKENS_PER_USER:
            midnight = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            today_total = func.coalesce(func.sum(func.coalesce(AiRequest.input_tokens, 0) + func.coalesce(AiRequest.output_tokens, 0)), 0)
            over_limit = len(
                (
                    await self.db.execute(
                        select(AiRequest.profile_id)
                        .where(AiRequest.created_at >= midnight, AiRequest.profile_id.is_not(None))
                        .group_by(AiRequest.profile_id)
                        .having(today_total >= settings.AI_DAILY_TOKENS_PER_USER)
                    )
                ).all()
            )

        return {
            "days": days,
            "requests": sum(m["requests"] for m in models),
            "failed": sum(m["failed"] for m in models),
            "input_tokens": sum(m["input_tokens"] for m in models),
            "output_tokens": sum(m["output_tokens"] for m in models),
            "estimated_cost_usd": round(sum(priced), 4) if priced else None,
            "unpriced_tokens": unpriced_tokens,
            "daily_limit_per_user": settings.AI_DAILY_TOKENS_PER_USER or None,
            "users_over_limit_today": over_limit,
            "by_model": [
                {**m, "estimated_cost_usd": None if m["estimated_cost_usd"] is None else round(m["estimated_cost_usd"], 4)}
                for m in models
            ],
            "by_purpose": [
                {"purpose": purpose, "requests": int(calls), "failed": int(fails), "tokens": int(tokens)}
                for purpose, calls, fails, tokens in purposes
            ],
            "daily": [
                {**row, "estimated_cost_usd": round(row["estimated_cost_usd"], 4)} for _, row in sorted(by_day.items())
            ],
            "top_users": [
                {"profile_id": str(pid), "name": name or "(unnamed)", "requests": int(calls), "tokens": int(tokens)}
                for pid, name, calls, tokens in users
            ],
        }

    # ---- links ------------------------------------------------------------------------------------------------

    async def links(self, limit: int = 30) -> dict:
        """What the link checker has found (see services/link_checker.py)."""
        counts = dict(
            (await self.db.execute(select(LinkCheck.status, func.count()).group_by(LinkCheck.status))).all()
        )
        latest = (await self.db.execute(select(func.max(LinkCheck.checked_at)))).scalar_one()
        dead = (
            await self.db.execute(
                select(LinkCheck)
                .where(LinkCheck.status == "dead")
                .order_by(LinkCheck.checked_at.desc())
                .limit(limit)
            )
        ).scalars().all()

        return {
            "ok": int(counts.get("ok", 0)),
            "dead": int(counts.get("dead", 0)),
            "unknown": int(counts.get("unknown", 0)),
            "last_checked": latest,
            "dead_links": [
                {
                    "url": row.url,
                    "http_status": row.http_status,
                    "reason": row.reason,
                    "fail_count": row.fail_count,
                    "checked_at": row.checked_at,
                }
                for row in dead
            ],
        }
