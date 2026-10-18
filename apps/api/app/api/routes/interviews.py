from uuid import UUID

from fastapi import APIRouter, Depends, Path, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.base import get_db
from app.schemas.interview import (
    AnswerRequest,
    SessionListResponse,
    SessionResponse,
    StartInterviewRequest,
    TurnResponse,
)
from app.services.interview_service import InterviewService

router = APIRouter(
    prefix="/interviews",
    tags=["Interview Coach"],
)


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_interview(
    payload: StartInterviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await InterviewService(db).start(payload, current_user.id)


@router.get("", response_model=SessionListResponse)
async def list_interviews(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await InterviewService(db).list(current_user.id)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_interview(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await InterviewService(db).get(session_id, current_user.id)


@router.post(
    "/{session_id}/turns/{order}/answer",
    response_model=TurnResponse,
)
async def answer_question(
    session_id: UUID,
    payload: AnswerRequest,
    order: int = Path(ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await InterviewService(db).answer(
        session_id, order, payload, current_user.id
    )


@router.post("/{session_id}/finish", response_model=SessionResponse)
async def finish_interview(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await InterviewService(db).finish(session_id, current_user.id)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interview(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    await InterviewService(db).delete(session_id, current_user.id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
