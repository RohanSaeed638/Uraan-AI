from uuid import UUID

from app.api.routes import settings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_settings import UserSettings


class SettingsRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_profile_id(
        self,
        profile_id: UUID,
    ) -> UserSettings | None:

        stmt = (
            select(UserSettings)
            .where(
                UserSettings.profile_id == profile_id
            )
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def create_default(
        self,
        profile_id: UUID,
    ) -> UserSettings:

        settings = UserSettings(
            profile_id=profile_id,
        )

        self.db.add(settings)

        await self.db.flush()

        return settings

    async def update(
        self,
        settings: UserSettings,
        updates: dict,
    ) -> UserSettings:

        for field, value in updates.items():
            setattr(settings, field, value)

        await self.db.flush()

        return settings        