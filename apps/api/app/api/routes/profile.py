from fastapi import APIRouter, Depends, HTTPException

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
):

    profile = await service.get_profile(current_user.id)

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Profile not found",
        )

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
