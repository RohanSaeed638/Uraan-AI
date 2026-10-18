from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.services import get_roadmap_service
from app.db.base import get_db
from app.api.dependencies import get_current_user
from app.schemas.learning import ContinueLearningResponse
from app.services.learning_service import get_continue_learning

from typing import Literal
from uuid import UUID

from app.schemas.learning import LearningAgendaResponse
from app.services.learning_service import get_learning_agenda


router = APIRouter(
    prefix="/learning",
    tags=["Learning"],
)


@router.get(
    "/continue",
    response_model=ContinueLearningResponse | None,
)
async def continue_learning(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_continue_learning(
        db=db,
        user_id=current_user.id,
    )

@router.get(
    "",
    response_model=LearningAgendaResponse,
)
async def list_learning(
    view: Literal["today", "week", "all"] = Query("today"),
    roadmap_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    roadmap_service=Depends(get_roadmap_service)
):
    selected_roadmap_id = roadmap_id

    if selected_roadmap_id is None:

        current_roadmap = await roadmap_service.get_current(
            auth_user_id=current_user.id,
        )

        if current_roadmap is None:
            return LearningAgendaResponse(view=view)

        selected_roadmap_id = current_roadmap.id

    return await get_learning_agenda(
        db=db,
        user_id=current_user.id,
        roadmap_id=selected_roadmap_id,
        view=view,
    )