from uuid import UUID

from fastapi import HTTPException

from app.core.analytics import track

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

    async def _check_career(self, slug: str | None):
        if slug and not await self.profile_repository.career_exists(slug):
            raise HTTPException(status_code=422, detail="Unknown career path")

    async def update_profile(
        self,
        auth_user_id: UUID,
        data: dict,
    ):
        await self._check_career(data.get("career_slug"))

        existed = await self.profile_repository.get_by_auth_user_id(auth_user_id)
        profile = await self.profile_repository.upsert(
            auth_user_id,
            data,
        )

        # The first save is the learner joining; finishing the questions is activation.
        if existed is None:
            track(profile.id, "profile_created", language=data.get("language"))

        if data.get("onboarding_completed") and not (existed and existed.onboarding_completed):
            track(profile.id, "onboarding_completed", career=data.get("career_slug"))

        return profile

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

        await self._check_career(changes.get("career_slug"))

        for field, value in changes.items():
            if value is None and field in REQUIRED_PROFILE_FIELDS:
                raise HTTPException(
                    status_code=422,
                    detail=f"{field} cannot be empty",
                )

            setattr(profile, field, value)

        return await self.profile_repository.update(profile)
    