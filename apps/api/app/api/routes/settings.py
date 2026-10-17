from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.services.settings_service import SettingsService
from app.schemas.settings import (
    UpdateUserSettingsRequest,
    UserSettingsResponse,
)
from app.api.dependencies import get_current_user

router = APIRouter(
    prefix="/settings",
    tags=["Settings"],
)


@router.get(
    "",
    response_model=UserSettingsResponse,
)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = SettingsService(db)

    return await service.get_settings(
        auth_user_id=current_user.id
    )

@router.patch(
    "",
    response_model=UserSettingsResponse,
)
async def update_settings(
    payload: UpdateUserSettingsRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = SettingsService(db)

    return await service.update_settings(
        payload=payload,
        auth_user_id=current_user.id,
    )