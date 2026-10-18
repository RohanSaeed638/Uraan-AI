from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.services.quiz_generator import QuizGenerator
from app.models.quiz import Quiz
from app.models.quiz_attempt import QuizAttempt
from app.models.quiz_question import QuizQuestion
from app.repositories.profile_repository import ProfileRepository
from app.repositories.quiz_repository import QuizRepository
from app.repositories.roadmap_task_repository import (
    RoadmapTaskRepository,
)
from app.schemas.quiz import (
    QuizSubmitRequest,
    QuizSubmitResponse,
    QuizAnswerResult,
    QuizQuestionResponse,
)


PASSING_PERCENTAGE = 70.0


class QuizService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_repository = ProfileRepository(db)
        self.quiz_repository = QuizRepository(db)
        self.task_repository = RoadmapTaskRepository(db)
        self.generator = QuizGenerator()

    async def _get_profile_and_validate_task(
        self,
        task_id: UUID,
        auth_user_id: UUID,
    ):
        profile = await (
            self.profile_repository
            .get_by_auth_user_id(auth_user_id)
        )

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found",
            )

        task = await self.quiz_repository.get_owned_task(
            task_id=task_id,
            profile_id=profile.id,
        )

        if not task:
            raise HTTPException(
                status_code=404,
                detail="Task not found",
            )

        return profile

    async def _generate_quiz(
        self,
        task_id: UUID,
        profile,
    ) -> list[QuizQuestion]:
        # Loads the task with its learning units, which the prompt uses.
        task = await self.task_repository.get_task_for_user(
            task_id=task_id,
            profile_id=profile.id,
        )

        try:
            output = await self.generator.generate(
                profile=profile,
                task=task,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail="Could not generate a quiz right now. Try again.",
            ) from exc

        quiz = Quiz(
            task_id=task_id,
            title=f"{task.title} quiz",
            passing_score=int(PASSING_PERCENTAGE),
        )

        try:
            await self.quiz_repository.create_quiz_with_questions(
                quiz=quiz,
                questions=[
                    QuizQuestion(
                        task_id=task_id,
                        question=item.question,
                        options=item.options,
                        correct_option=item.correct_option,
                        explanation=item.explanation,
                        order=index,
                    )
                    for index, item in enumerate(output.questions)
                ],
            )
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        return await self.quiz_repository.get_questions(task_id)

    async def get_questions(
        self,
        task_id: UUID,
        auth_user_id: UUID,
    ) -> list[QuizQuestionResponse]:

        profile = await self._get_profile_and_validate_task(
            task_id,
            auth_user_id,
        )

        questions = await self.quiz_repository.get_questions(
            task_id
        )

        if not questions:
            questions = await self._generate_quiz(
                task_id=task_id,
                profile=profile,
            )

        return [
            QuizQuestionResponse(
                id=question.id,
                question=question.question,
                options=question.options,
                order=question.order,
            )
            for question in questions
        ]

    async def submit(
        self,
        task_id: UUID,
        payload: QuizSubmitRequest,
        auth_user_id: UUID,
    ) -> QuizSubmitResponse:

        profile = await self._get_profile_and_validate_task(
            task_id,
            auth_user_id,
        )

        questions = await self.quiz_repository.get_questions(
            task_id
        )

        if not questions:
            raise HTTPException(
                status_code=404,
                detail="No quiz questions found for this task",
            )

        question_map = {
            question.id: question
            for question in questions
        }

        submitted_ids = [
            answer.question_id
            for answer in payload.answers
        ]

        if len(submitted_ids) != len(set(submitted_ids)):
            raise HTTPException(
                status_code=422,
                detail="Duplicate question answers are not allowed",
            )

        if set(submitted_ids) != set(question_map):
            raise HTTPException(
                status_code=422,
                detail="Submit exactly one answer for every quiz question",
            )

        results = []
        correct_count = 0

        for answer in payload.answers:
            question = question_map[answer.question_id]

            if answer.selected_option >= len(question.options):
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid option for question {question.id}",
                )

            is_correct = (
                answer.selected_option == question.correct_option
            )

            if is_correct:
                correct_count += 1

            results.append(
                QuizAnswerResult(
                    question_id=question.id,
                    selected_option=answer.selected_option,
                    correct_option=question.correct_option,
                    is_correct=is_correct,
                    explanation=question.explanation,
                )
            )

        total = len(questions)

        score = round(
            (correct_count / total) * 100,
            2,
        )

        passed = score >= PASSING_PERCENTAGE

        attempt = QuizAttempt(
            profile_id=profile.id,
            task_id=task_id,
            answers=[
                answer.model_dump(mode="json")
                for answer in payload.answers
            ],
            total_questions=total,
            correct_answers=correct_count,
            score_percentage=score,
            passed=passed,
        )

        try:
            await self.quiz_repository.create_attempt(attempt)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        return QuizSubmitResponse(
            attempt_id=attempt.id,
            task_id=task_id,
            total_questions=total,
            correct_answers=correct_count,
            score_percentage=score,
            passed=passed,
            passing_percentage=PASSING_PERCENTAGE,
            results=results,
        )