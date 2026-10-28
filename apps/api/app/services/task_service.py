from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.task_repository import list_user_tasks


async def get_user_tasks(
    db: AsyncSession,
    user_id: UUID,
    roadmap_id: UUID | None = None,
    status: str | None = None,
):
    if status not in (None, "todo", "completed"):
        raise ValueError("Unsupported task status")

    completed = None

    if status == "todo":
        completed = False
    elif status == "completed":
        completed = True

    return await list_user_tasks(
        db=db,
        user_id=user_id,
        roadmap_id=roadmap_id,
        completed=completed,
    )