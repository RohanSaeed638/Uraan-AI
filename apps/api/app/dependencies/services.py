from fastapi import Depends

from app.dependencies.profile import get_profile_repository
from app.repositories.profile_repository import ProfileRepository
from app.services.profile_service import ProfileService


def get_profile_service(
    repository: ProfileRepository = Depends(
        get_profile_repository
    ),
):
    return ProfileService(repository)