from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.api.dependencies import get_current_user

from app.schemas.progress import (
    ProgressOverviewResponse,
)

from app.services.progress_service import (
    get_progress_overview,
)

router = APIRouter(
    prefix="/progress",
    tags=["Progress"],
)


@router.get(
    "/overview",
    response_model=ProgressOverviewResponse,
)
async def progress_overview(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_progress_overview(
        db=db,
        user_id=current_user.id,
    )