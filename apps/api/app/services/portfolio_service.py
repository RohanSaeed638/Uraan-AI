import re
from app.services.achievement_service import AchievementService
from app.ai.llm import use_profile
import secrets
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.services.portfolio_generator import PortfolioGenerator
from app.models.portfolio import PortfolioProject
from app.repositories.portfolio_repository import PortfolioRepository
from app.repositories.profile_repository import ProfileRepository
from app.schemas.portfolio import (
    CHECKLIST,
    ChecklistItem,
    ChecklistUpdateRequest,
    CreateProjectRequest,
    DraftDescriptionResponse,
    PortfolioResponse,
    ProjectFields,
    ProjectResponse,
    PublicPortfolioResponse,
    PublicProject,
    Suggestion,
    UpdatePortfolioRequest,
)

MAX_PROJECTS = 30


def slugify(name: str | None) -> str:
    """A URL-safe base from the first name, e.g. "Rohan Saeed" -> "rohan"."""
    first = (name or "").split()[0] if (name or "").split() else "learner"
    base = re.sub(r"[^a-z0-9]+", "-", first.lower()).strip("-")

    return (base or "learner")[:30]


def checklist_items(state: dict | None) -> list[ChecklistItem]:
    state = state or {}

    return [
        ChecklistItem(id=item_id, label=label, done=bool(state.get(item_id)))
        for item_id, label in CHECKLIST
    ]


class PortfolioService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_repository = ProfileRepository(db)
        self.repository = PortfolioRepository(db)
        self.generator = PortfolioGenerator()

    async def _profile(self, auth_user_id: UUID):
        profile = await self.profile_repository.get_by_auth_user_id(
            auth_user_id
        )

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        return profile

    async def _project(self, project_id: UUID, profile_id: UUID):
        project = await self.repository.get_project(project_id, profile_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        return project

    async def _commit(self):
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise HTTPException(
                status_code=409,
                detail="That conflicts with something you already saved.",
            ) from exc
        except Exception:
            await self.db.rollback()
            raise

    async def _response(self, profile, portfolio) -> PortfolioResponse:
        projects = await self.repository.list_projects(profile.id)
        suggestions = await self.repository.suggestions(profile.id)

        return PortfolioResponse(
            headline=portfolio.headline,
            bio=portfolio.bio,
            slug=portfolio.slug,
            is_public=portfolio.is_public,
            projects=[ProjectResponse.model_validate(p) for p in projects],
            checklist=checklist_items(portfolio.checklist),
            suggestions=[
                Suggestion(unit_id=row[0], title=row[1], task_title=row[2])
                for row in suggestions
            ],
        )

    async def get(self, auth_user_id: UUID) -> PortfolioResponse:
        profile = await self._profile(auth_user_id)
        portfolio = await self.repository.get_or_create(profile.id)
        await self._commit()

        return await self._response(profile, portfolio)

    async def _free_slug(self, profile) -> str:
        base = slugify(profile.full_name)

        for _ in range(10):
            candidate = f"{base}-{secrets.token_hex(2)}"
            if not await self.repository.slug_taken(candidate, profile.id):
                return candidate

        raise HTTPException(status_code=500, detail="Could not pick an address")

    async def update(
        self,
        payload: UpdatePortfolioRequest,
        auth_user_id: UUID,
    ) -> PortfolioResponse:
        profile = await self._profile(auth_user_id)
        portfolio = await self.repository.get_or_create(profile.id)

        changes = payload.model_dump(exclude_unset=True)

        if changes.get("slug") is not None and await self.repository.slug_taken(
            changes["slug"], profile.id
        ):
            raise HTTPException(
                status_code=409, detail="That address is already taken."
            )

        for field in ("headline", "bio", "slug"):
            if field in changes:
                setattr(portfolio, field, changes[field])

        if changes.get("is_public") is not None:
            if changes["is_public"] and not portfolio.slug:
                portfolio.slug = await self._free_slug(profile)
            portfolio.is_public = changes["is_public"]

        await AchievementService(self.db).safe_evaluate(profile)
        await self._commit()

        return await self._response(profile, portfolio)

    async def set_checklist(
        self,
        payload: ChecklistUpdateRequest,
        auth_user_id: UUID,
    ) -> PortfolioResponse:
        profile = await self._profile(auth_user_id)
        portfolio = await self.repository.get_or_create(profile.id)

        # Reassign so SQLAlchemy sees the JSON column as changed.
        portfolio.checklist = {
            **(portfolio.checklist or {}),
            payload.item_id: payload.done,
        }

        await self._commit()

        return await self._response(profile, portfolio)

    async def create_project(
        self,
        payload: CreateProjectRequest,
        auth_user_id: UUID,
    ) -> ProjectResponse:
        profile = await self._profile(auth_user_id)

        if await self.repository.count_projects(profile.id) >= MAX_PROJECTS:
            raise HTTPException(
                status_code=409,
                detail=f"You can add up to {MAX_PROJECTS} projects.",
            )

        values = payload.model_dump(exclude_unset=True)
        source_id = values.pop("source_unit_id", None)

        title = values.get("title")
        description = values.get("description")

        if source_id is not None:
            found = await self.repository.owned_project_unit(
                source_id, profile.id
            )

            if not found:
                raise HTTPException(
                    status_code=404, detail="Project lesson not found"
                )

            unit, _ = found

            if not unit.completed:
                raise HTTPException(
                    status_code=422,
                    detail="Complete the project lesson before adding it.",
                )

            title = title or unit.title
            description = description if description is not None else unit.description

        if not title:
            raise HTTPException(status_code=422, detail="A title is required")

        project = PortfolioProject(
            profile_id=profile.id,
            source_unit_id=source_id,
            title=title,
            description=description,
            repo_url=values.get("repo_url"),
            live_url=values.get("live_url"),
            tech=values.get("tech") or [],
            visible=values.get("visible", True),
            position=await self.repository.count_projects(profile.id),
        )

        await self.repository.add_project(project)
        await self._commit()
        await self.db.refresh(project)

        return ProjectResponse.model_validate(project)

    async def update_project(
        self,
        project_id: UUID,
        payload: ProjectFields,
        auth_user_id: UUID,
    ) -> ProjectResponse:
        profile = await self._profile(auth_user_id)
        project = await self._project(project_id, profile.id)

        for field, value in payload.model_dump(exclude_unset=True).items():
            if field in ("title", "visible", "tech") and value is None:
                raise HTTPException(
                    status_code=422, detail=f"{field} cannot be empty"
                )
            setattr(project, field, value)

        await self._commit()
        await self.db.refresh(project)

        return ProjectResponse.model_validate(project)

    async def delete_project(
        self,
        project_id: UUID,
        auth_user_id: UUID,
    ) -> None:
        profile = await self._profile(auth_user_id)
        project = await self._project(project_id, profile.id)

        await self.repository.delete_project(project)
        await self._commit()

    async def draft_description(
        self,
        project_id: UUID,
        auth_user_id: UUID,
    ) -> DraftDescriptionResponse:
        profile = await self._profile(auth_user_id)
        use_profile(profile.id, profile.language)
        project = await self._project(project_id, profile.id)

        brief = task_title = None

        if project.source_unit_id:
            found = await self.repository.owned_project_unit(
                project.source_unit_id, profile.id
            )
            if found:
                unit, task = found
                brief, task_title = unit.content or unit.description, task.title

        try:
            description = await self.generator.draft_description(
                title=project.title,
                tech=list(project.tech or []),
                task_title=task_title,
                brief=brief,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail="Could not write a description right now. Try again.",
            ) from exc

        return DraftDescriptionResponse(description=description)

    async def public(self, slug: str) -> PublicPortfolioResponse:
        found = await self.repository.get_public(slug.lower())

        # Same answer for a missing or private portfolio.
        if not found:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        portfolio, profile = found
        projects = await self.repository.list_projects(profile.id)

        return PublicPortfolioResponse(
            name=profile.full_name or "Learner",
            headline=portfolio.headline,
            bio=portfolio.bio,
            projects=[
                PublicProject.model_validate(p) for p in projects if p.visible
            ],
        )
