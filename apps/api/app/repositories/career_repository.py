from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.career import Career


class CareerRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(
        self,
        *,
        search: str | None,
        difficulty: str | None,
        demand: str | None,
        category: str | None,
        min_salary: int | None,
        max_salary: int | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Career], int]:
        query = select(Career).where(Career.is_active.is_(True))

        if search:
            like = f"%{search.strip()}%"
            query = query.where(
                or_(Career.name.ilike(like), Career.description.ilike(like))
            )
        if difficulty:
            query = query.where(Career.difficulty == difficulty)
        if demand:
            query = query.where(Career.market_demand == demand)
        if category:
            query = query.where(Career.category == category)
        # A career matches when its salary range overlaps the asked range.
        if min_salary is not None:
            query = query.where(Career.salary_max_pkr >= min_salary)
        if max_salary is not None:
            query = query.where(Career.salary_min_pkr <= max_salary)

        total = (
            await self.db.execute(
                select(func.count()).select_from(query.subquery())
            )
        ).scalar_one()

        rows = (
            await self.db.execute(
                query.order_by(Career.name)
                .limit(page_size)
                .offset((page - 1) * page_size)
            )
        ).scalars().all()

        return list(rows), total

    async def get_by_slug(self, slug: str) -> Career | None:
        return (
            await self.db.execute(
                select(Career).where(
                    Career.slug == slug, Career.is_active.is_(True)
                )
            )
        ).scalar_one_or_none()

    async def get_many(self, slugs: list[str]) -> dict[str, Career]:
        rows = (
            await self.db.execute(
                select(Career).where(
                    Career.slug.in_(slugs), Career.is_active.is_(True)
                )
            )
        ).scalars().all()

        return {career.slug: career for career in rows}

    async def list_active(self) -> list[Career]:
        return list(
            (
                await self.db.execute(
                    select(Career)
                    .where(Career.is_active.is_(True))
                    .order_by(Career.name)
                )
            ).scalars()
        )
