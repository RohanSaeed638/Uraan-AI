from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resource import Resource


class ResourceRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        resource: Resource,
    ) -> Resource:

        self.db.add(resource)

        await self.db.commit()

        await self.db.refresh(resource)

        return resource

    async def get_by_lesson(
        self,
        lesson_id,
    ):

        result = await self.db.execute(
            select(Resource).where(
                Resource.lesson_id == lesson_id
            )
        )

        return result.scalars().all()