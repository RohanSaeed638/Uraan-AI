from uuid import UUID

from fastapi import HTTPException

from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile import REQUIRED_PROFILE_FIELDS

class ProfileService:

    def __init__(
        self,
        profile_repository: ProfileRepository,
    ):
        self.profile_repository = profile_repository

    async def get_profile(
        self,
        auth_user_id: UUID,
    ):
        return await self.profile_repository.get_by_auth_user_id(
            auth_user_id
        )

    async def update_profile(
        self,
        auth_user_id: UUID,
        data: dict,
    ):
        return await self.profile_repository.upsert(
            auth_user_id,
            data,
        )

    async def patch_profile(
        self,
        auth_user_id: UUID,
        changes: dict,
    ):
        """Applies only the supplied fields to an existing profile."""
        profile = await self.profile_repository.get_by_auth_user_id(
            auth_user_id
        )

        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        for field, value in changes.items():
            if value is None and field in REQUIRED_PROFILE_FIELDS:
                raise HTTPException(
                    status_code=422,
                    detail=f"{field} cannot be empty",
                )

            setattr(profile, field, value)

        return await self.profile_repository.update(profile)
    