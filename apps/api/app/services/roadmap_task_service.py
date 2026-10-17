# from uuid import UUID

# from app.repositories.roadmap_task_repository import RoadmapTaskRepository


# class RoadmapTaskService:

#     def __init__(
#         self,
#         repository: RoadmapTaskRepository,
#     ):
#         self.repository = repository

#     async def get_task(
#         self,
#         task_id: UUID,
#     ):
#         return await self.repository.get_by_id(task_id)

#     async def update_completion(
#         self,
#         task_id: UUID,
#         completed: bool,
#     ):
#         return await self.repository.update_task_completion(
#             task_id=task_id,
#             completed=completed,
#         )

#     async def get_progress(
#         self,
#         roadmap_id: UUID,
#     ):
#         return await self.repository.get_roadmap_progress(
#             roadmap_id=roadmap_id,
#         )


from uuid import UUID

from fastapi import HTTPException

from app.repositories.profile_repository import ProfileRepository
from app.repositories.roadmap_task_repository import (
    RoadmapTaskRepository,
)


class RoadmapTaskService:

    def __init__(
        self,
        db,
    ):
        self.db = db

        self.repository = RoadmapTaskRepository(db)
        self.profile_repository = ProfileRepository(db)

    async def get_task(
        self,
        task_id: UUID,
        auth_user_id: UUID,
    ):

        profile = await (
            self.profile_repository
            .get_by_auth_user_id(auth_user_id)
        )

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found",
            )

        task = await (
            self.repository
            .get_task_for_user(
                task_id=task_id,
                profile_id=profile.id,
            )
        )

        if not task:
            raise HTTPException(
                status_code=404,
                detail="Task not found",
            )

        return task

    async def update_completion(
        self,
        task_id: UUID,
        completed: bool,
        auth_user_id: UUID,
    ):

        profile = await (
            self.profile_repository
            .get_by_auth_user_id(auth_user_id)
        )

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found",
            )

        task = await (
            self.repository
            .get_task_for_user(
                task_id=task_id,
                profile_id=profile.id,
            )
        )

        if not task:
            raise HTTPException(
                status_code=404,
                detail="Task not found",
            )

        task.completed = completed

        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def get_progress(
        self,
        roadmap_id: UUID,
    ):
        return await self.repository.get_roadmap_progress(
            roadmap_id=roadmap_id,
        )