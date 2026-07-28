from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile


class ProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_auth_user_id(
        self,
        auth_user_id: UUID,
    ) -> Profile | None:
        result = await self.db.execute(
            select(Profile).where(
                Profile.auth_user_id == auth_user_id
            ).order_by(
                    Profile.created_at.desc()   
                    )
        )

        return result.scalars().first()

    async def create(
        self,
        profile: Profile,
    ) -> Profile:
        self.db.add(profile)

        await self.db.commit()

        await self.db.refresh(profile)

        return profile

    async def update(
        self,
        profile: Profile,
    ) -> Profile:
        await self.db.commit()

        await self.db.refresh(profile)

        return profile

    async def upsert(
        self,
        auth_user_id: UUID,
        data: dict,
    ) -> Profile:

        profile = await self.get_by_auth_user_id(auth_user_id)

        if profile is None:

            profile = Profile(
                auth_user_id=auth_user_id,
                **data,
            )

            return await self.create(profile)

        for key, value in data.items():
            setattr(profile, key, value)

        return await self.update(profile)