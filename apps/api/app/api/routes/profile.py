from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.services.admin_service import make_admin_if_listed

from app.api.dependencies import get_current_user
from app.dependencies.services import get_profile_service

from app.schemas.auth import CurrentUser
from app.schemas.profile import (
    PatchProfileRequest,
    ProfileResponse,
    UpdateProfileRequest,
)

from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get(
    "/me",
    response_model=ProfileResponse,
)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
    db: AsyncSession = Depends(get_db),
):

    profile = await service.get_profile(current_user.id)

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Profile not found",
        )

    # An address in ADMIN_EMAILS becomes an admin as soon as it signs in, so the
    # app can show the Admin link right away.
    await make_admin_if_listed(db, profile, getattr(current_user, "email", None))

    return profile


@router.put(
    "/me",
    response_model=ProfileResponse,
)
async def update_me(
    request: UpdateProfileRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):

    profile = await service.update_profile(
        current_user.id,
        request.model_dump(),
    )

    return profile


@router.patch(
    "/me",
    response_model=ProfileResponse,
)
async def patch_me(
    request: PatchProfileRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    return await service.patch_profile(
        current_user.id,
        request.model_dump(exclude_unset=True),
    )
