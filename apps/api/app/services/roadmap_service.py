from fastapi import HTTPException
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.services.roadmap_generator import RoadmapGenerator
from app.repositories.profile_repository import ProfileRepository
from app.repositories.roadmap_repository import RoadmapRepository
from app.models.enums import RoadmapStatus
from app.repositories.roadmap_task_repository import RoadmapTaskRepository

class RoadmapService:

    def __init__(
        self,
        db: AsyncSession,
    ):

        self.db = db
        self.roadmap_task_repository = RoadmapTaskRepository(db)
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

    async def get_by_id(
        self,
        roadmap_id: UUID,
        user_id: UUID,
    ):

        roadmap = await self.roadmap_repository.get_by_id(
            roadmap_id=roadmap_id,
            user_id=user_id
        )

        if not roadmap:
            raise HTTPException(
                status_code=404,
                detail="Roadmap not found or does not belong to the user.",
            )

        return roadmap


    async def update_task_completion(
        self,
        task_id: UUID,
        completed: bool,
    ):

        task = await self.roadmap_task_repository.update_task_completion(
            task_id,
            completed,
        )

        if not task:
            raise HTTPException(
                status_code=404,
                detail="Task not found",
            )

        progress = await self.roadmap_task_repository.get_roadmap_progress(
            task.phase.roadmap_id,
        )

        if (
            progress["total"] > 0
            and progress["completed"] == progress["total"]
        ):
            await self.roadmap_repository.update_status(
                task.phase.roadmap_id,
                RoadmapStatus.COMPLETED,
            )

        return task    

    async def get_all(
        self,
        auth_user_id: UUID,
    ):

        profile = await self.profile_repository.get_by_auth_user_id(
            auth_user_id
        )

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found",
            )

        roadmaps = await self.roadmap_repository.get_all_by_user(
            profile.id
        )

        summaries = []

        for roadmap in roadmaps:

            progress = await self.roadmap_task_repository.get_roadmap_progress(
                roadmap.id
            )

            percentage = 0

            if progress["total"] > 0:
                percentage = int(
                    progress["completed"]
                    * 100
                    / progress["total"]
                )

            summaries.append(
                {
                    "id": roadmap.id,
                    "title": roadmap.title,
                    "description": roadmap.description,
                    "status": roadmap.status,
                    "progress": percentage,
                    "completed_tasks": progress["completed"],
                    "total_tasks": progress["total"],
                    "updated_at": roadmap.updated_at,
                }
            )

        return summaries