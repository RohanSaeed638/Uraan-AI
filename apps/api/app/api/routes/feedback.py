from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.base import get_db
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/learning-units", tags=["Feedback"])


@router.get("/{unit_id}/feedback", response_model=FeedbackResponse | None)
async def get_feedback(
    unit_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """The learner's own vote on this lesson, or null."""
    return await FeedbackService(db).get(unit_id, current_user.id)


@router.put("/{unit_id}/feedback", response_model=FeedbackResponse)
async def put_feedback(
    unit_id: UUID,
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await FeedbackService(db).save(unit_id, request, current_user.id)


@router.delete("/{unit_id}/feedback", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feedback(
    unit_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    await FeedbackService(db).clear(unit_id, current_user.id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
