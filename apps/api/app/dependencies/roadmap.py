from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.repositories.roadmap_repository import RoadmapRepository


def get_roadmap_repository(
    db: AsyncSession = Depends(get_db),
):
    return RoadmapRepository(db)