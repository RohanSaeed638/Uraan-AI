import re
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.library_repository import SORTS, LibraryRepository
from app.repositories.profile_repository import ProfileRepository

TYPES = {"course", "video", "docs", "book", "practice"}
LEVELS = {"beginner", "intermediate", "advanced"}

# Words that say nothing about a topic, so they never make a resource relevant.
STOP_WORDS = {
    "the", "and", "for", "with", "learn", "learning", "build", "basics",
    "introduction", "intro", "to", "of", "a", "an", "in", "on", "your", "how",
    "using", "use", "guide", "tutorial", "course", "from", "into", "web",
}


def words(text: str | None) -> set[str]:
    return {
        w
        for w in re.findall(r"[a-z0-9+#.]+", (text or "").lower())
        if len(w) > 1 and w not in STOP_WORDS
    }


def rank_for_task(resources: list[dict], task_title: str, task_description: str | None, limit: int) -> list[dict]:
    """The career's resources that best match a task: more words in common
    with the task come first; ties go to the better rated, then to title."""
    wanted = words(task_title) | words(task_description)

    def score(resource: dict) -> int:
        text = f"{resource['title']} {resource.get('provider') or ''}"
        return len(wanted & words(text))

    ranked = sorted(
        resources,
        key=lambda r: (-score(r), -(r["avg_rating"] or 0), r["title"]),
    )

    return ranked[:limit]


class LibraryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = LibraryRepository(db)
        self.profiles = ProfileRepository(db)

    async def _profile_id(self, auth_user_id) -> UUID:
        profile = await self.profiles.get_by_auth_user_id(auth_user_id)

        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        return profile.id

    async def search(self, auth_user_id, **filters):
        if filters.get("type") and filters["type"] not in TYPES:
            raise HTTPException(status_code=422, detail="Unknown resource type")
        if filters.get("difficulty") and filters["difficulty"] not in LEVELS:
            raise HTTPException(status_code=422, detail="Unknown difficulty")
        if filters["sort"] not in SORTS:
            raise HTTPException(status_code=422, detail="Unknown sort order")

        profile_id = await self._profile_id(auth_user_id)
        items, total = await self.repository.search(profile_id, **filters)

        return {
            "items": items,
            "total": total,
            "page": filters["page"],
            "page_size": filters["page_size"],
        }

    async def _existing(self, profile_id: UUID, resource_id: UUID) -> None:
        if await self.repository.get(profile_id, resource_id) is None:
            raise HTTPException(status_code=404, detail="Resource not found")

    async def _change(self, auth_user_id, resource_id: UUID, action):
        profile_id = await self._profile_id(auth_user_id)
        await self._existing(profile_id, resource_id)

        await action(profile_id, resource_id)
        await self.db.commit()

        return await self.repository.get(profile_id, resource_id)

    async def bookmark(self, auth_user_id, resource_id):
        return await self._change(auth_user_id, resource_id, self.repository.add_bookmark)

    async def unbookmark(self, auth_user_id, resource_id):
        return await self._change(auth_user_id, resource_id, self.repository.remove_bookmark)

    async def rate(self, auth_user_id, resource_id, rating: int):
        async def action(profile_id, rid):
            await self.repository.set_rating(profile_id, rid, rating)

        return await self._change(auth_user_id, resource_id, action)

    async def clear_rating(self, auth_user_id, resource_id):
        return await self._change(auth_user_id, resource_id, self.repository.remove_rating)

    async def recommended_for_task(self, auth_user_id, task_id: UUID, limit: int = 4):
        profile_id = await self._profile_id(auth_user_id)
        context = await self.repository.task_context(profile_id, task_id)

        if context is None:
            raise HTTPException(status_code=404, detail="Task not found")

        task, career = context

        if not career:
            return []

        resources = await self.repository.for_career(profile_id, career)

        return rank_for_task(resources, task.title, task.description, limit)
