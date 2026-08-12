from uuid import UUID

from app.repositories.roadmap_task_repository import RoadmapTaskRepository


class RoadmapTaskService:

    def __init__(
        self,
        repository: RoadmapTaskRepository,
    ):
        self.repository = repository

    async def get_task(
        self,
        task_id: UUID,
    ):
        return await self.repository.get_by_id(task_id)

    async def update_completion(
        self,
        task_id: UUID,
        completed: bool,
    ):
        return await self.repository.update_task_completion(
            task_id=task_id,
            completed=completed,
        )

    async def get_progress(
        self,
        roadmap_id: UUID,
    ):
        return await self.repository.get_roadmap_progress(
            roadmap_id=roadmap_id,
        )