from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.models.user_settings import UserSettings
from app.repositories.profile_repository import ProfileRepository
from app.repositories.settings_repository import SettingsRepository
from app.schemas.settings import (
    UpdateUserSettingsRequest,
    UserSettingsResponse,
)
from sqlalchemy import select
from app.models.profile import Profile

class SettingsService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_repository = ProfileRepository(db)
        self.settings_repository = SettingsRepository(db)

    async def get_settings(
        self,
        auth_user_id: UUID,
    ) -> UserSettingsResponse:

        profile = await (
            self.profile_repository
            .get_by_auth_user_id(auth_user_id)
        )

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found",
            )

        settings = await (
            self.settings_repository
            .get_by_profile_id(profile.id)
        )

        if not settings:
            try:
                # Safe when multiple first-time GET requests
                # arrive for the same profile.
                stmt = (
                    insert(UserSettings)
                    .values(profile_id=profile.id)
                    .on_conflict_do_nothing(
                        index_elements=["profile_id"]
                    )
                )

                await self.db.execute(stmt)
                await self.db.commit()

            except Exception:
                await self.db.rollback()
                raise

            settings = await (
                self.settings_repository
                .get_by_profile_id(profile.id)
            )

        if not settings:
            raise HTTPException(
                status_code=500,
                detail="Unable to load user settings",
            )

        return UserSettingsResponse.model_validate(
            settings
        )

    async def update_settings(
        self,
        payload: UpdateUserSettingsRequest,
        auth_user_id: UUID,
    ) -> UserSettingsResponse:

        profile = await (
            self.profile_repository
            .get_by_auth_user_id(auth_user_id)
        )

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found",
            )

        updates = payload.model_dump(exclude_unset=True)

        # An empty PATCH is valid and leaves settings unchanged.
        if not updates:
            return await self.get_settings(auth_user_id)

        try:
            # Lock the profile to serialize first-time settings
            # creation and updates for the same user.
            await self.db.execute(
                select(Profile.id)
                .where(Profile.id == profile.id)
                .with_for_update()
            )

            settings = await (
                self.settings_repository
                .get_by_profile_id(profile.id)
            )

            if not settings:
                settings = await (
                    self.settings_repository
                    .create_default(profile.id)
                )

            settings = await (
                self.settings_repository.update(
                    settings=settings,
                    updates=updates,
                )
            )

            await self.db.commit()
            await self.db.refresh(settings)

            return UserSettingsResponse.model_validate(settings)

        except Exception:
            await self.db.rollback()
            raise    