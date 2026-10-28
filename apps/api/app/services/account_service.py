from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio import Portfolio, PortfolioProject
from app.models.roadmap import Roadmap
from app.models.user_settings import UserSettings
from app.repositories.mentor_repository import MentorRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.roadmap_task_repository import RoadmapTaskRepository
from app.schemas.document import DocumentResponse
from app.schemas.portfolio import CHECKLIST
from app.schemas.profile import ProfileResponse
from app.schemas.settings import UserSettingsResponse
from app.repositories.document_repository import DocumentRepository
from app.services.gamification_service import GamificationService
from app.services.interview_service import InterviewService

# Large enough for any real history; keeps the file and the work bounded.
MAX_CONVERSATIONS = 200


def _enum(value):
    return getattr(value, "value", value)


class AccountService:
    """Everything stored about one user, as a single JSON document."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_repository = ProfileRepository(db)

    async def export(self, auth_user_id: UUID) -> dict:
        profile = await self.profile_repository.get_by_auth_user_id(
            auth_user_id
        )

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        return {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "profile": ProfileResponse.model_validate(profile).model_dump(
                mode="json"
            ),
            "settings": await self._settings(profile.id),
            "gamification": await GamificationService(self.db).summary(profile),
            "roadmaps": await self._roadmaps(profile.id),
            "documents": await self._documents(profile.id),
            "portfolio": await self._portfolio(profile.id),
            "interviews": await self._interviews(auth_user_id),
            "mentor_conversations": await self._mentor(profile.id),
        }

    async def _settings(self, profile_id: UUID) -> dict | None:
        row = (
            await self.db.execute(
                select(UserSettings).where(UserSettings.profile_id == profile_id)
            )
        ).scalar_one_or_none()

        if row is None:
            return None

        return UserSettingsResponse.model_validate(row).model_dump(mode="json")

    async def _roadmaps(self, profile_id: UUID) -> list[dict]:
        rows = (
            await self.db.execute(
                select(Roadmap)
                .where(Roadmap.profile_id == profile_id)
                .order_by(Roadmap.created_at.asc())
            )
        ).scalars().all()

        tasks = RoadmapTaskRepository(self.db)
        out = []

        for roadmap in rows:
            progress = await tasks.get_roadmap_progress(roadmap.id)

            out.append(
                {
                    "id": str(roadmap.id),
                    "title": roadmap.title,
                    "description": roadmap.description,
                    "status": _enum(roadmap.status),
                    "career_slug": roadmap.career_slug,
                    "skill_level": _enum(roadmap.skill_level),
                    "learning_style": _enum(roadmap.learning_style),
                    "learning_goal": roadmap.learning_goal,
                    "created_at": roadmap.created_at.isoformat(),
                    "tasks_total": progress["total"],
                    "tasks_completed": progress["completed"],
                }
            )

        return out

    async def _documents(self, profile_id: UUID) -> list[dict]:
        rows = await DocumentRepository(self.db).list_for_profile(profile_id)

        return [
            DocumentResponse.model_validate(r).model_dump(mode="json")
            for r in rows
        ]

    async def _portfolio(self, profile_id: UUID) -> dict | None:
        portfolio = (
            await self.db.execute(
                select(Portfolio).where(Portfolio.profile_id == profile_id)
            )
        ).scalar_one_or_none()

        projects = (
            await self.db.execute(
                select(PortfolioProject)
                .where(PortfolioProject.profile_id == profile_id)
                .order_by(PortfolioProject.position.asc())
            )
        ).scalars().all()

        if portfolio is None and not projects:
            return None

        return {
            "headline": portfolio.headline if portfolio else None,
            "bio": portfolio.bio if portfolio else None,
            "slug": portfolio.slug if portfolio else None,
            "is_public": bool(portfolio and portfolio.is_public),
            "checklist": [
                {
                    "id": item_id,
                    "label": label,
                    "done": bool((portfolio.checklist or {}).get(item_id))
                    if portfolio
                    else False,
                }
                for item_id, label in CHECKLIST
            ],
            "projects": [
                {
                    "title": p.title,
                    "description": p.description,
                    "repo_url": p.repo_url,
                    "live_url": p.live_url,
                    "tech": list(p.tech or []),
                    "visible": p.visible,
                }
                for p in projects
            ],
        }

    async def _interviews(self, auth_user_id: UUID) -> list[dict]:
        service = InterviewService(self.db)
        listing = await service.list(auth_user_id)

        return [
            (await service.get(item.id, auth_user_id)).model_dump(mode="json")
            for item in listing.sessions
        ]

    async def _mentor(self, profile_id: UUID) -> list[dict]:
        repo = MentorRepository(self.db)
        conversations = await repo.list_conversations(
            profile_id=profile_id, limit=MAX_CONVERSATIONS, offset=0
        )

        out = []

        for conversation in conversations:
            messages = await repo.get_conversation_messages(conversation.id)

            out.append(
                {
                    "title": conversation.title,
                    "created_at": conversation.created_at.isoformat(),
                    "messages": [
                        {
                            "role": m.role,
                            "content": m.content,
                            "created_at": m.created_at.isoformat(),
                        }
                        for m in messages
                    ],
                }
            )

        return out
