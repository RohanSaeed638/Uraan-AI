from typing import Literal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.repositories.project_repository import (
    list_user_projects,
    get_user_project_by_id,
)

from app.schemas.project import (
    ProjectResponse,
    ProjectListResponse,
    ProjectContextResponse,
    ProjectDetailResponse,
)

def project_meta(unit) -> dict:
    """Difficulty, skills and portfolio value (older projects have none)."""
    details = unit.details or {}

    return {
        "difficulty": details.get("difficulty"),
        "skills": list(details.get("skills") or []),
        "portfolio_value": details.get("portfolio_value"),
    }


ProjectStatus = Literal[
    "all",
    "pending",
    "completed",
]


async def get_user_projects(
    db: AsyncSession,
    user_id: UUID,
    roadmap_id: UUID | None = None,
    status: ProjectStatus = "all",
) -> ProjectListResponse:

    completed_filter = None

    if status == "completed":
        completed_filter = True

    elif status == "pending":
        completed_filter = False

    rows = await list_user_projects(
        db=db,
        user_id=user_id,
        roadmap_id=roadmap_id,
        completed=completed_filter,
    )

    projects = []

    for roadmap, phase, task, unit in rows:
        projects.append(
            ProjectResponse(
                id=unit.id,
                title=unit.title,
                description=unit.description,

                roadmap_id=roadmap.id,
                roadmap_title=roadmap.title,

                phase_id=phase.id,
                phase_title=phase.title,

                task_id=task.id,
                task_title=task.title,

                estimated_minutes=unit.estimated_minutes,
                completed=unit.completed,
                day=unit.day,
                **project_meta(unit),
            )
        )

    completed_count = sum(
        1 for project in projects
        if project.completed
    )

    return ProjectListResponse(
        total=len(projects),
        completed=completed_count,
        pending=len(projects) - completed_count,
        projects=projects,
    )



async def get_project_detail(
    db: AsyncSession,
    user_id: UUID,
    project_id: UUID,
) -> ProjectDetailResponse:

    result = await get_user_project_by_id(
        db=db,
        user_id=user_id,
        project_id=project_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    roadmap, phase, task, unit = result

    return ProjectDetailResponse(
        id=unit.id,
        title=unit.title,
        description=unit.description,
        instructions=unit.content,
        resource_url=unit.resource_url,
        estimated_minutes=unit.estimated_minutes,
        day=unit.day,
        completed=unit.completed,
        **project_meta(unit),

        roadmap=ProjectContextResponse(
            id=roadmap.id,
            title=roadmap.title,
        ),

        phase=ProjectContextResponse(
            id=phase.id,
            title=phase.title,
        ),

        task=ProjectContextResponse(
            id=task.id,
            title=task.title,
        ),
    )