from app.services.roadmap_service import RoadmapService
from app.db.base import get_db
from app.services.roadmap_task_service import RoadmapTaskService
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.profile import get_profile_repository
from app.repositories.profile_repository import ProfileRepository
from app.services.profile_service import ProfileService
from app.services.task_learning_unit_service import (
    TaskLearningUnitService,
)

def get_profile_service(
    repository: ProfileRepository = Depends(
        get_profile_repository
    ),
):
    return ProfileService(repository)

def get_roadmap_service(
     db: AsyncSession = Depends(get_db),
):
    return RoadmapService(db)

def get_roadmap_task_service(
    db: AsyncSession = Depends(get_db),
):
    return RoadmapTaskService(db)

def get_task_learning_unit_service(
    db: AsyncSession = Depends(get_db),
):
    return TaskLearningUnitService(db)