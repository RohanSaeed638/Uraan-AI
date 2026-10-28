from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.dependencies.services import (
    get_task_learning_unit_service,
)
from app.schemas.roadmap import (
    LearningUnitResponse,
    UpdateLearningUnitRequest,
)
from app.services.task_learning_unit_service import (
    TaskLearningUnitService,
)


router = APIRouter(
    prefix="/learning-units",
    tags=["Learning Units"],
)

@router.get(
    "/{learning_unit_id}",
    response_model=LearningUnitResponse,
)
async def get_learning_unit(
    learning_unit_id: UUID,
    current_user=Depends(get_current_user),
    service: TaskLearningUnitService = Depends(
        get_task_learning_unit_service
    ),
):
    return await service.get_by_id(
        learning_unit_id,
        current_user.id,
    )

@router.patch(
    "/{learning_unit_id}",
    response_model=LearningUnitResponse,
)
async def update_learning_unit(
    learning_unit_id: UUID,
    payload: UpdateLearningUnitRequest,
    current_user=Depends(get_current_user),
    service: TaskLearningUnitService = Depends(
        get_task_learning_unit_service
    ),
):
    return await service.update_completion(
        learning_unit_id=learning_unit_id,
        completed=payload.completed,
        auth_user_id=current_user.id,
    )