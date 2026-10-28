from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.services.quiz_service import QuizService
from app.schemas.quiz import (
    QuizSubmitRequest,
    QuizSubmitResponse,
    QuizQuestionResponse,
)
from app.api.dependencies import get_current_user  


router = APIRouter(
    prefix="/tasks",
    tags=["Quizzes"],
)


@router.get(
    "/{task_id}/quiz",
    response_model=list[QuizQuestionResponse],
)
async def get_task_quiz(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = QuizService(db)

    return await service.get_questions(
        task_id=task_id,
        auth_user_id=current_user.id,
    )


@router.post(
    "/{task_id}/quiz/submit",
    response_model=QuizSubmitResponse,
)
async def submit_task_quiz(
    task_id: UUID,
    payload: QuizSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = QuizService(db)

    return await service.submit(
        task_id=task_id,
        payload=payload,
        auth_user_id=current_user.id,
    )