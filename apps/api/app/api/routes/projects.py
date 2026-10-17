from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db

from app.schemas.project import ProjectListResponse
from app.services.project_service import get_user_projects
from app.api.dependencies import get_current_user
from app.schemas.project import ProjectDetailResponse
from app.services.project_service import get_project_detail



router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


@router.get(
    "",
    response_model=ProjectListResponse,
)
async def list_projects(
    roadmap_id: UUID | None = Query(default=None),
    status: Literal[
        "all",
        "pending",
        "completed",
    ] = Query(default="all"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_user_projects(
        db=db,
        user_id=current_user.id,
        roadmap_id=roadmap_id,
        status=status,
    )

@router.get(
    "/{project_id}",
    response_model=ProjectDetailResponse,
)
async def retrieve_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_project_detail(
        db=db,
        user_id=current_user.id,
        project_id=project_id,
    )
