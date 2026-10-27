from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.library import LibraryResource, ResourceBookmark, ResourceRating
from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask

SORTS = {"recommended", "rating", "title", "newest"}


class LibraryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _base(self, profile_id: UUID):
        """Resources with their average rating, count, and this learner's
        bookmark and rating, as one query."""
        stats = (
            select(
                ResourceRating.resource_id.label("rid"),
                func.avg(ResourceRating.rating).label("avg"),
                func.count().label("cnt"),
            )
            .group_by(ResourceRating.resource_id)
            .subquery()
        )
        mine = (
            select(ResourceRating.resource_id.label("rid"), ResourceRating.rating.label("r"))
            .where(ResourceRating.profile_id == profile_id)
            .subquery()
        )
        saved = (
            select(ResourceBookmark.resource_id.label("rid"))
            .where(ResourceBookmark.profile_id == profile_id)
            .subquery()
        )

        return (
            select(
                LibraryResource,
                stats.c.avg,
                func.coalesce(stats.c.cnt, 0),
                saved.c.rid.is_not(None),
                mine.c.r,
            )
            .outerjoin(stats, stats.c.rid == LibraryResource.id)
            .outerjoin(mine, mine.c.rid == LibraryResource.id)
            .outerjoin(saved, saved.c.rid == LibraryResource.id)
            .where(LibraryResource.is_active.is_(True)),
            stats,
        )

    @staticmethod
    def _row(row) -> dict:
        resource, avg, count, bookmarked, mine = row

        return {
            "id": resource.id,
            "title": resource.title,
            "url": resource.url,
            "type": resource.type,
            "provider": resource.provider,
            "description": resource.description,
            "is_free": resource.is_free,
            "difficulty": resource.difficulty,
            "career_slugs": list(resource.career_slugs or []),
            "avg_rating": round(float(avg), 1) if avg is not None else None,
            "rating_count": int(count or 0),
            "bookmarked": bool(bookmarked),
            "my_rating": mine,
        }

    async def search(
        self,
        profile_id: UUID,
        *,
        q: str | None,
        career: str | None,
        type: str | None,
        free_only: bool,
        difficulty: str | None,
        bookmarked_only: bool,
        sort: str,
        page: int,
        page_size: int,
    ) -> tuple[list[dict], int]:
        stmt, stats = self._base(profile_id)

        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(
                or_(
                    LibraryResource.title.ilike(like),
                    LibraryResource.provider.ilike(like),
                    LibraryResource.description.ilike(like),
                )
            )
        if career:
            stmt = stmt.where(LibraryResource.career_slugs.any(career))
        if type:
            stmt = stmt.where(LibraryResource.type == type)
        if free_only:
            stmt = stmt.where(LibraryResource.is_free.is_(True))
        if difficulty:
            stmt = stmt.where(LibraryResource.difficulty == difficulty)
        if bookmarked_only:
            stmt = stmt.where(
                LibraryResource.id.in_(
                    select(ResourceBookmark.resource_id).where(
                        ResourceBookmark.profile_id == profile_id
                    )
                )
            )

        total = (
            await self.db.execute(select(func.count()).select_from(stmt.subquery()))
        ).scalar_one()

        if sort == "title":
            order = [LibraryResource.title]
        elif sort == "newest":
            order = [LibraryResource.created_at.desc(), LibraryResource.title]
        else:  # "recommended" and "rating": best rated first, unrated after
            order = [stats.c.avg.desc().nulls_last(), stats.c.cnt.desc().nulls_last(), LibraryResource.title]

        rows = (
            await self.db.execute(
                stmt.order_by(*order).limit(page_size).offset((page - 1) * page_size)
            )
        ).all()

        return [self._row(r) for r in rows], total

    async def get(self, profile_id: UUID, resource_id: UUID) -> dict | None:
        stmt, _ = self._base(profile_id)
        row = (
            await self.db.execute(stmt.where(LibraryResource.id == resource_id))
        ).first()

        return self._row(row) if row else None

    # ---- bookmarks and ratings ----------------------------------------------------

    async def add_bookmark(self, profile_id: UUID, resource_id: UUID) -> None:
        await self.db.execute(
            insert(ResourceBookmark)
            .values(profile_id=profile_id, resource_id=resource_id)
            .on_conflict_do_nothing(index_elements=["profile_id", "resource_id"])
        )

    async def remove_bookmark(self, profile_id: UUID, resource_id: UUID) -> None:
        await self.db.execute(
            delete(ResourceBookmark).where(
                ResourceBookmark.profile_id == profile_id,
                ResourceBookmark.resource_id == resource_id,
            )
        )

    async def set_rating(self, profile_id: UUID, resource_id: UUID, rating: int) -> None:
        stmt = insert(ResourceRating).values(
            profile_id=profile_id, resource_id=resource_id, rating=rating
        )
        await self.db.execute(
            stmt.on_conflict_do_update(
                index_elements=["profile_id", "resource_id"],
                set_={"rating": rating},
            )
        )

    async def remove_rating(self, profile_id: UUID, resource_id: UUID) -> None:
        await self.db.execute(
            delete(ResourceRating).where(
                ResourceRating.profile_id == profile_id,
                ResourceRating.resource_id == resource_id,
            )
        )

    # ---- recommendations for a task ---------------------------------------------------

    async def task_context(self, profile_id: UUID, task_id: UUID):
        """(task, career slug) if this learner owns the task, else None."""
        row = (
            await self.db.execute(
                select(RoadmapTask, Roadmap.career_slug)
                .join(RoadmapPhase, RoadmapPhase.id == RoadmapTask.phase_id)
                .join(Roadmap, Roadmap.id == RoadmapPhase.roadmap_id)
                .where(RoadmapTask.id == task_id, Roadmap.profile_id == profile_id)
            )
        ).first()

        return (row[0], row[1]) if row else None

    async def for_career(self, profile_id: UUID, career: str) -> list[dict]:
        stmt, _ = self._base(profile_id)
        rows = (
            await self.db.execute(stmt.where(LibraryResource.career_slugs.any(career)))
        ).all()

        return [self._row(r) for r in rows]
