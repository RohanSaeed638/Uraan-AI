from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.base import get_db
from app.schemas.portfolio import (
    ChecklistUpdateRequest,
    CreateProjectRequest,
    DraftDescriptionResponse,
    PortfolioResponse,
    ProjectFields,
    ProjectResponse,
    PublicPortfolioResponse,
    UpdatePortfolioRequest,
)
from app.services.portfolio_service import PortfolioService

router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio"],
)


# Declared before the "/{project_id}" routes so "public" is never read
# as a project id.
@router.get("/public/{slug}", response_model=PublicPortfolioResponse)
async def public_portfolio(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Unauthenticated; only portfolios the owner made public."""
    return await PortfolioService(db).public(slug)


@router.get("", response_model=PortfolioResponse)
async def get_portfolio(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await PortfolioService(db).get(current_user.id)


@router.patch("", response_model=PortfolioResponse)
async def update_portfolio(
    payload: UpdatePortfolioRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await PortfolioService(db).update(payload, current_user.id)


@router.patch("/checklist", response_model=PortfolioResponse)
async def update_checklist(
    payload: ChecklistUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await PortfolioService(db).set_checklist(payload, current_user.id)


@router.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    payload: CreateProjectRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await PortfolioService(db).create_project(payload, current_user.id)


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    payload: ProjectFields,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await PortfolioService(db).update_project(
        project_id, payload, current_user.id
    )


@router.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    await PortfolioService(db).delete_project(project_id, current_user.id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/projects/{project_id}/draft",
    response_model=DraftDescriptionResponse,
)
async def draft_project_description(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await PortfolioService(db).draft_description(
        project_id, current_user.id
    )
