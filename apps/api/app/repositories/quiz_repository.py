from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.quiz import Quiz
from uuid import UUID

from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.models.quiz_question import QuizQuestion
from app.models.quiz_attempt import QuizAttempt

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


    async def get_owned_task(
        self,
        task_id: UUID,
        profile_id: UUID,
    ) -> RoadmapTask | None:

        stmt = (
            select(RoadmapTask)
            .join(
                RoadmapPhase,
                RoadmapTask.phase_id == RoadmapPhase.id,
            )
            .join(
                Roadmap,
                RoadmapPhase.roadmap_id == Roadmap.id,
            )
            .where(
                RoadmapTask.id == task_id,
                Roadmap.profile_id == profile_id,
            )
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_questions(
        self,
        task_id: UUID,
    ) -> list[QuizQuestion]:

        stmt = (
            select(QuizQuestion)
            .where(QuizQuestion.task_id == task_id)
            .order_by(
                QuizQuestion.order,
                QuizQuestion.id,
            )
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_attempt(
        self,
        attempt: QuizAttempt,
    ) -> QuizAttempt:

        self.db.add(attempt)
        await self.db.flush()

        return attempt
    