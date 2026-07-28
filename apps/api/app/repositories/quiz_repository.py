from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import Quiz


class QuizRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        quiz: Quiz,
    ) -> Quiz:

        self.db.add(quiz)

        await self.db.commit()

        await self.db.refresh(quiz)

        return quiz

    async def get_by_lesson(
        self,
        lesson_id,
    ):

        result = await self.db.execute(
            select(Quiz).where(
                Quiz.lesson_id == lesson_id
            )
        )

        return result.scalars().all()