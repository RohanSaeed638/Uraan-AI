from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.base import get_db
from app.schemas.library import RatingRequest, ResourceItem, ResourceListResponse
from app.services.library_service import LibraryService

router = APIRouter(prefix="/resources", tags=["Resources"])


@router.get("", response_model=ResourceListResponse)
async def list_resources(
    q: str | None = Query(default=None, max_length=100),
    career: str | None = Query(default=None, max_length=100),
    type: str | None = None,
    difficulty: str | None = None,
    free_only: bool = False,
    bookmarked: bool = False,
    sort: str = "recommended",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await LibraryService(db).search(
        current_user.id,
        q=q,
        career=career,
        type=type,
        difficulty=difficulty,
        free_only=free_only,
        bookmarked_only=bookmarked,
        sort=sort,
        page=page,
        page_size=page_size,
    )


# Defined before "/{resource_id}/..." so "recommended" is not read as an id.
@router.get("/recommended", response_model=list[ResourceItem])
async def recommended_for_task(
    task_id: UUID,
    limit: int = Query(default=4, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await LibraryService(db).recommended_for_task(
        current_user.id, task_id, limit
    )


@router.post("/{resource_id}/bookmark", response_model=ResourceItem)
async def bookmark_resource(
    resource_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await LibraryService(db).bookmark(current_user.id, resource_id)


@router.delete("/{resource_id}/bookmark", response_model=ResourceItem)
async def unbookmark_resource(
    resource_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await LibraryService(db).unbookmark(current_user.id, resource_id)


@router.put("/{resource_id}/rating", response_model=ResourceItem)
async def rate_resource(
    resource_id: UUID,
    data: RatingRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await LibraryService(db).rate(current_user.id, resource_id, data.rating)


@router.delete("/{resource_id}/rating", response_model=ResourceItem)
async def clear_resource_rating(
    resource_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await LibraryService(db).clear_rating(current_user.id, resource_id)
