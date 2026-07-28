from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson import Lesson


class LessonRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        lesson: Lesson,
    ) -> Lesson:

        self.db.add(lesson)

        await self.db.commit()

        await self.db.refresh(lesson)

        return lesson

    async def get_by_milestone(
        self,
        milestone_id,
    ):

        result = await self.db.execute(
            select(Lesson).where(
                Lesson.milestone_id == milestone_id
            )
        )

        return result.scalars().all()