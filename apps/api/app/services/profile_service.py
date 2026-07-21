from uuid import UUID

from app.repositories.profile_repository import ProfileRepository

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
    