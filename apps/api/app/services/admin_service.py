"""The admin portal: what staff can see and change.

Every change is written to `audit_logs` in the same transaction, so a change
and its record stand or fall together. Nothing is deleted for good: careers,
resources and announcements are switched off instead, because learners'
roadmaps, bookmarks and notifications point at them.
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, literal, or_, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.admin import Announcement, AuditLog
from app.models.ai_request import AiRequest
from app.models.career import Career, CareerResource, CareerSkill
from app.models.library import LibraryResource
from app.models.notification import Notification
from app.models.profile import Profile
from app.schemas.admin import (
    AnnouncementCreate,
    AnnouncementUpdate,
    CareerCreate,
    CareerUpdate,
    ResourceFields,
)

STATS_DAYS = 7
AUDIT_PAGE = 50
TYPE_ANNOUNCEMENT = "announcement"


def snapshot(obj, fields: list[str]) -> dict:
    return {field: getattr(obj, field) for field in fields}


def diff(before: dict, after: dict) -> dict:
    """{"field": [before, after]} for what really changed."""
    return {k: [before.get(k), after[k]] for k in after if before.get(k) != after[k]}


class AdminService:
    def __init__(self, db: AsyncSession, actor: Profile, actor_email: str | None = None):
        self.db = db
        self.actor = actor
        self.actor_email = actor_email

    # ---- the record ------------------------------------------------------------------------------------------------

    def log(self, action: str, target_type: str, target_id, summary: str, changes: dict | None = None):
        label = f"{self.actor.full_name} <{self.actor_email}>" if self.actor_email else self.actor.full_name

        self.db.add(
            AuditLog(
                actor_profile_id=self.actor.id,
                actor_label=label[:300],
                action=action,
                target_type=target_type,
                target_id=str(target_id) if target_id else None,
                summary=summary[:300],
                changes=jsonable_encoder(changes) if changes else None,
            )
        )

    async def audit(self, limit: int = AUDIT_PAGE, before: datetime | None = None, action: str | None = None):
        query = select(AuditLog)

        if before is not None:
            query = query.where(AuditLog.created_at < before)

        if action:
            query = query.where(AuditLog.action.like(f"{action}%"))

        rows = (
            await self.db.execute(query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(limit + 1))
        ).scalars().all()

        return {
            "items": [
                {
                    "id": r.id,
                    "at": r.created_at,
                    "actor": r.actor_label,
                    "action": r.action,
                    "target_type": r.target_type,
                    "target_id": r.target_id,
                    "summary": r.summary,
                    "changes": r.changes,
                }
                for r in rows[:limit]
            ],
            "has_more": len(rows) > limit,
        }

    # ---- the numbers -------------------------------------------------------------------------------------------

    async def stats(self, days: int = STATS_DAYS) -> dict:
        since = datetime.now(timezone.utc) - timedelta(days=days)

        async def scalar(sql: str, **params) -> int:
            return int((await self.db.execute(text(sql), params)).scalar_one() or 0)

        counts = {
            "users": await scalar("select count(*) from profiles"),
            "new_users_7d": await scalar("select count(*) from profiles where created_at >= :s", s=since),
            "active_users_7d": await scalar(
                "select count(distinct profile_id) from xp_events where created_at >= :s", s=since
            ),
            "roadmaps": await scalar("select count(*) from roadmaps"),
            "lessons_completed": await scalar("select count(*) from task_learning_units where completed"),
            "tasks_completed": await scalar("select count(*) from roadmap_tasks where completed"),
            "mentor_messages": await scalar("select count(*) from mentor_messages where role = 'user'"),
        }

        by_purpose = (
            await self.db.execute(
                select(
                    AiRequest.purpose,
                    func.count().label("n"),
                    func.count().filter(AiRequest.success.is_(False)).label("bad"),
                    func.avg(AiRequest.latency_ms).label("ms"),
                )
                .where(AiRequest.created_at >= since)
                .group_by(AiRequest.purpose)
                .order_by(func.count().desc())
            )
        ).all()

        by_provider = (
            await self.db.execute(
                select(
                    AiRequest.provider,
                    func.count().label("n"),
                    func.count().filter(AiRequest.success.is_(False)).label("bad"),
                )
                .where(AiRequest.created_at >= since)
                .group_by(AiRequest.provider)
                .order_by(func.count().desc())
            )
        ).all()

        failures = (
            await self.db.execute(
                select(AiRequest)
                .where(AiRequest.created_at >= since, AiRequest.success.is_(False))
                .order_by(AiRequest.created_at.desc())
                .limit(15)
            )
        ).scalars().all()

        return {
            "counts": counts,
            "days": days,
            "ai_requests": sum(r.n for r in by_purpose),
            "ai_failures": sum(r.bad for r in by_purpose),
            "ai_by_purpose": [
                {
                    "purpose": r.purpose,
                    "requests": r.n,
                    "failures": r.bad,
                    "failure_rate": round(r.bad / r.n, 3) if r.n else 0.0,
                    "avg_latency_ms": int(r.ms) if r.ms is not None else None,
                }
                for r in by_purpose
            ],
            "ai_by_provider": [{"provider": r.provider, "requests": r.n, "failures": r.bad} for r in by_provider],
            "recent_failures": [
                {"at": f.created_at, "purpose": f.purpose, "provider": f.provider, "error_type": f.error_type}
                for f in failures
            ],
        }

    # ---- users -------------------------------------------------------------------------------------------------------------

    async def users(self, search: str | None, limit: int, offset: int) -> dict:
        like = f"%{search.strip()}%" if search and search.strip() else None
        where = "where (cast(:q as text) is null or p.full_name ilike cast(:q as text) or u.email ilike cast(:q as text))"

        total = int(
            (
                await self.db.execute(
                    text(f"select count(*) from profiles p left join auth.users u on u.id = p.auth_user_id {where}"),
                    {"q": like},
                )
            ).scalar_one()
        )

        rows = (
            await self.db.execute(
                text(
                    "select p.id, p.full_name, u.email, p.role, p.language, p.career_slug, p.xp, p.streak_days, "
                    "p.created_at, p.last_activity_date, "
                    "(select count(*) from roadmaps r where r.profile_id = p.id) as roadmaps "
                    f"from profiles p left join auth.users u on u.id = p.auth_user_id {where} "
                    "order by p.created_at desc limit :l offset :o"
                ),
                {"q": like, "l": limit, "o": offset},
            )
        ).mappings().all()

        return {
            "items": [
                {
                    "id": r["id"],
                    "name": r["full_name"],
                    "email": r["email"],
                    "role": r["role"],
                    "language": r["language"],
                    "career_slug": r["career_slug"],
                    "xp": r["xp"] or 0,
                    "streak_days": r["streak_days"] or 0,
                    "roadmaps": int(r["roadmaps"]),
                    "created_at": r["created_at"],
                    "last_activity_date": r["last_activity_date"].isoformat() if r["last_activity_date"] else None,
                }
                for r in rows
            ],
            "total": total,
        }

    async def set_role(self, profile_id: UUID, role: str) -> dict:
        target = (await self.db.execute(select(Profile).where(Profile.id == profile_id))).scalar_one_or_none()

        if target is None:
            raise HTTPException(status_code=404, detail="User not found")

        if target.role == role:
            return {"id": target.id, "role": role}

        if role != "admin" and target.role == "admin":
            admins = (
                await self.db.execute(select(func.count()).select_from(Profile).where(Profile.role == "admin"))
            ).scalar_one()

            if target.id == self.actor.id:
                raise HTTPException(status_code=409, detail="You cannot remove your own admin access.")

            if admins <= 1:
                raise HTTPException(status_code=409, detail="There must be at least one admin.")

        before = target.role
        target.role = role
        self.log("user.role", "user", target.id, f"{target.full_name}: {before} to {role}", {"role": [before, role]})
        await self.db.commit()

        return {"id": target.id, "role": role}

    # ---- careers -----------------------------------------------------------------------------------------------------------

    CAREER_FIELDS = [
        "name", "description", "category", "icon", "color", "difficulty", "estimated_months",
        "salary_min_pkr", "salary_max_pkr", "market_demand", "is_active",
    ]

    async def careers(self) -> list[dict]:
        rows = (
            await self.db.execute(
                select(
                    Career,
                    select(func.count()).where(CareerSkill.career_id == Career.id).correlate(Career).scalar_subquery(),
                    select(func.count()).where(CareerResource.career_id == Career.id).correlate(Career).scalar_subquery(),
                ).order_by(Career.name)
            )
        ).all()

        return [
            {
                "id": c.id, "slug": c.slug, "name": c.name, "category": c.category, "difficulty": c.difficulty,
                "market_demand": c.market_demand, "is_active": c.is_active, "skills": skills, "resources": resources,
            }
            for c, skills, resources in rows
        ]

    async def career(self, career_id: UUID) -> Career:
        career = (await self.db.execute(select(Career).where(Career.id == career_id))).scalar_one_or_none()

        if career is None:
            raise HTTPException(status_code=404, detail="Career not found")

        return career

    def _apply_career(self, career: Career, data: CareerUpdate | CareerCreate):
        try:
            data.check_salary()
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

        for field in self.CAREER_FIELDS:
            setattr(career, field, getattr(data, field))

        career.skills = [CareerSkill(name=s.name, order_number=i) for i, s in enumerate(data.skills)]
        career.resources = [
            CareerResource(
                title=r.title, type=r.type, provider=r.provider, url=r.url,
                is_free=r.is_free, difficulty=r.difficulty, order_number=i,
            )
            for i, r in enumerate(data.resources)
        ]

    async def create_career(self, data: CareerCreate) -> Career:
        taken = (await self.db.execute(select(Career.id).where(Career.slug == data.slug))).first()

        if taken:
            raise HTTPException(status_code=409, detail="A career with this address already exists.")

        career = Career(slug=data.slug)
        self._apply_career(career, data)
        self.db.add(career)
        await self.db.flush()
        self.log("career.create", "career", career.id, f"Created career {career.name}")
        await self.db.commit()
        await self.db.refresh(career)

        return career

    async def update_career(self, career_id: UUID, data: CareerUpdate) -> Career:
        career = await self.career(career_id)
        before = snapshot(career, self.CAREER_FIELDS)
        before["skills"] = [s.name for s in career.skills]
        before["resources"] = [r.title for r in career.resources]

        self._apply_career(career, data)

        after = snapshot(career, self.CAREER_FIELDS)
        after["skills"] = [s.name for s in career.skills]
        after["resources"] = [r.title for r in career.resources]
        changes = diff(before, after)

        if changes:
            what = "Switched off" if changes.get("is_active") == [True, False] else "Updated"
            self.log("career.update", "career", career.id, f"{what} career {career.name}", changes)

        await self.db.commit()
        await self.db.refresh(career)

        return career

    # ---- library resources ---------------------------------------------------------------------------------

    RESOURCE_FIELDS = [
        "title", "url", "type", "provider", "description", "is_free", "difficulty",
        "career_slugs", "language", "is_active",
    ]

    async def resources(self, search: str | None, active: bool | None, limit: int, offset: int) -> dict:
        query = select(LibraryResource)

        if search and search.strip():
            like = f"%{search.strip()}%"
            query = query.where(or_(LibraryResource.title.ilike(like), LibraryResource.provider.ilike(like)))

        if active is not None:
            query = query.where(LibraryResource.is_active.is_(active))

        total = (await self.db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
        rows = (
            await self.db.execute(query.order_by(LibraryResource.title).limit(limit).offset(offset))
        ).scalars().all()

        return {"items": list(rows), "total": total}

    async def _check_careers(self, slugs: list[str]):
        if not slugs:
            return

        found = set(
            (await self.db.execute(select(Career.slug).where(Career.slug.in_(slugs)))).scalars()
        )
        missing = sorted(set(slugs) - found)

        if missing:
            raise HTTPException(status_code=422, detail=f"Unknown careers: {', '.join(missing)}")

    async def _resource(self, resource_id: UUID) -> LibraryResource:
        row = (
            await self.db.execute(select(LibraryResource).where(LibraryResource.id == resource_id))
        ).scalar_one_or_none()

        if row is None:
            raise HTTPException(status_code=404, detail="Resource not found")

        return row

    async def _url_free(self, url: str, except_id: UUID | None = None):
        query = select(LibraryResource.id).where(LibraryResource.url == url)

        if except_id:
            query = query.where(LibraryResource.id != except_id)

        if (await self.db.execute(query)).first():
            raise HTTPException(status_code=409, detail="A resource with this link already exists.")

    async def create_resource(self, data: ResourceFields) -> LibraryResource:
        await self._check_careers(data.career_slugs)
        await self._url_free(data.url)

        row = LibraryResource(**data.model_dump())
        self.db.add(row)
        await self.db.flush()
        self.log("resource.create", "resource", row.id, f"Added resource {row.title}")
        await self.db.commit()
        await self.db.refresh(row)

        return row

    async def update_resource(self, resource_id: UUID, data: ResourceFields) -> LibraryResource:
        row = await self._resource(resource_id)
        await self._check_careers(data.career_slugs)
        await self._url_free(data.url, row.id)

        new = data.model_dump()
        changes = diff(snapshot(row, self.RESOURCE_FIELDS), new)

        for field, value in new.items():
            setattr(row, field, value)

        if changes:
            what = "Switched off" if changes.get("is_active") == [True, False] else "Updated"
            self.log("resource.update", "resource", row.id, f"{what} resource {row.title}", changes)

        await self.db.commit()
        await self.db.refresh(row)

        return row

    # ---- announcements ------------------------------------------------------------------------------------------

    async def announcements(self) -> list[Announcement]:
        return list(
            (await self.db.execute(select(Announcement).order_by(Announcement.created_at.desc(), Announcement.id.desc()).limit(100))).scalars()
        )

    async def publish(self, data: AnnouncementCreate) -> Announcement:
        now = datetime.now(timezone.utc)

        if data.ends_at is not None and data.ends_at <= now:
            raise HTTPException(status_code=422, detail="The end time must be in the future.")

        row = Announcement(
            title=data.title, body=data.body, level=data.level, starts_at=now,
            ends_at=data.ends_at, created_by=self.actor.id,
        )
        self.db.add(row)
        await self.db.flush()

        if data.notify:
            row.notified = await self._notify_everyone(row)

        self.log(
            "announcement.publish", "announcement", row.id,
            f"Published \"{row.title}\"" + (f" and notified {row.notified} learners" if data.notify else ""),
        )
        await self.db.commit()
        await self.db.refresh(row)

        return row

    async def _notify_everyone(self, row: Announcement) -> int:
        """One notification per learner, in a single statement. Safe to repeat:
        the unique key makes a second run add nothing."""
        result = await self.db.execute(
            insert(Notification)
            .from_select(
                ["id", "profile_id", "type", "title", "body", "url", "dedupe_key"],
                select(
                    func.gen_random_uuid(),
                    Profile.id,
                    literal(TYPE_ANNOUNCEMENT),
                    literal(row.title[:200]),
                    literal(row.body),
                    literal("/dashboard"),
                    literal(f"announcement:{row.id}"),
                ),
            )
            .on_conflict_do_nothing(constraint="uq_notification_once")
            .returning(Notification.id)
        )

        return len(result.all())

    async def update_announcement(self, announcement_id: UUID, data: AnnouncementUpdate) -> Announcement:
        row = (
            await self.db.execute(select(Announcement).where(Announcement.id == announcement_id))
        ).scalar_one_or_none()

        if row is None:
            raise HTTPException(status_code=404, detail="Announcement not found")

        changes = {}

        for field in data.model_fields_set:
            value = getattr(data, field)

            if getattr(row, field) != value:
                changes[field] = [getattr(row, field), value]
                setattr(row, field, value)

        if changes:
            self.log("announcement.update", "announcement", row.id, f"Updated \"{row.title}\"", changes)

        await self.db.commit()
        await self.db.refresh(row)

        return row


async def active_announcements(db: AsyncSession) -> list[Announcement]:
    """What learners see now: switched on, started, not ended."""
    now = datetime.now(timezone.utc)

    return list(
        (
            await db.execute(
                select(Announcement)
                .where(
                    Announcement.is_active.is_(True),
                    or_(Announcement.starts_at.is_(None), Announcement.starts_at <= now),
                    or_(Announcement.ends_at.is_(None), Announcement.ends_at > now),
                )
                .order_by(Announcement.created_at.desc(), Announcement.id.desc())
                .limit(3)
            )
        ).scalars()
    )


async def make_admin_if_listed(db: AsyncSession, profile: Profile, email: str | None) -> bool:
    """The first admins come from ADMIN_EMAILS: signing in with a listed address
    makes the account an admin the first time it reaches an admin endpoint."""
    if profile.role == "admin":
        return True

    if email and email.lower() in settings.admin_emails:
        profile.role = "admin"
        db.add(
            AuditLog(
                actor_profile_id=profile.id,
                actor_label=f"{profile.full_name} <{email}>"[:300],
                action="user.role",
                target_type="user",
                target_id=str(profile.id),
                summary=f"{profile.full_name}: user to admin (listed in ADMIN_EMAILS)",
                changes={"role": ["user", "admin"]},
            )
        )
        await db.commit()

        return True

    return False
