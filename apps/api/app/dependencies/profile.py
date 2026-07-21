from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.repositories.profile_repository import ProfileRepository


def get_profile_repository(
    db: AsyncSession = Depends(get_db),
):
    return ProfileRepository(db)