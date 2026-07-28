from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.services.roadmap_generator import RoadmapGenerator
from app.repositories.profile_repository import ProfileRepository
from app.repositories.roadmap_repository import RoadmapRepository


class RoadmapService:

    def __init__(
        self,
        db: AsyncSession,
    ):

        self.db = db

        self.profile_repository = ProfileRepository(db)

        self.roadmap_repository = RoadmapRepository(db)

        self.generator = RoadmapGenerator()

    async def generate(
    self,
    auth_user_id,
    ):
        profile = await self.profile_repository.get_by_auth_user_id(auth_user_id)

        if not profile:
            raise ValueError("Profile not found for the given user ID.")

        roadmap_data = await self.generator.generate(profile)

        roadmap = await self.roadmap_repository.create(
            profile=profile,
            roadmap_data=roadmap_data.model_dump(),
        )

        return roadmap    

async def get_current(
        self,
        auth_user_id,
    ):

        profile = await self.profile_repository.get_by_auth_user_id(
            auth_user_id
        )

        if profile is None:
            raise Exception("Profile not found")

        return await self.roadmap_repository.get_latest(
            profile.id
        )    