from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.base import get_db
from app.schemas.career import (
    CareerDetail,
    CareerListResponse,
    CompareRequest,
    CompareResponse,
    RecommendRequest,
    RecommendResponse,
)
from app.services.career_service import CareerService

router = APIRouter(prefix="/careers", tags=["Careers"])


# The catalogue is public: visitors can browse before signing up.
@router.get("", response_model=CareerListResponse)
async def list_careers(
    search: str | None = Query(default=None, max_length=100),
    difficulty: str | None = None,
    demand: str | None = None,
    category: str | None = None,
    min_salary: int | None = Query(default=None, ge=0),
    max_salary: int | None = Query(default=None, ge=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    return await CareerService(db).search(
        search=search,
        difficulty=difficulty,
        demand=demand,
        category=category,
        min_salary=min_salary,
        max_salary=max_salary,
        page=page,
        page_size=page_size,
    )


@router.post("/compare", response_model=CompareResponse)
async def compare_careers(
    data: CompareRequest,
    db: AsyncSession = Depends(get_db),
):
    return await CareerService(db).compare(data.slugs)


@router.post("/recommend", response_model=RecommendResponse)
async def recommend_careers(
    data: RecommendRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await CareerService(db).recommend(
        current_user.id, data.model_dump()
    )


@router.get("/{slug}", response_model=CareerDetail)
async def get_career(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    return await CareerService(db).get(slug)
