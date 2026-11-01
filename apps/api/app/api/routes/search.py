from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.base import get_db
from app.services.search_service import MAX_LENGTH, SearchService

router = APIRouter(prefix="/search", tags=["Search"])


class SearchResult(BaseModel):
    kind: str
    id: UUID
    title: str
    subtitle: str | None = None
    url: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


@router.get("", response_model=SearchResponse)
async def search(
    q: str = Query(default="", max_length=MAX_LENGTH),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Results from the learner's own roadmaps, tasks, lessons, documents and
    mentor chats, and from the careers and resource library. Under two letters
    there is nothing to look for, so the answer is an empty list."""
    return {
        "query": q.strip(),
        "results": await SearchService(db).search(current_user.id, q),
    }
