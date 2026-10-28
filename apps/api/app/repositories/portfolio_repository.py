from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio import Portfolio, PortfolioProject
from app.models.profile import Profile
from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.models.task_learning_unit import TaskLearningUnit


class PortfolioRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self, profile_id: UUID) -> Portfolio:
        await self.db.execute(
            insert(Portfolio)
            .values(profile_id=profile_id, checklist={})
            .on_conflict_do_nothing(index_elements=["profile_id"])
        )

        result = await self.db.execute(
            select(Portfolio).where(Portfolio.profile_id == profile_id)
        )

        return result.scalar_one()

    async def slug_taken(self, slug: str, except_profile_id: UUID) -> bool:
        result = await self.db.execute(
            select(Portfolio.id).where(
                Portfolio.slug == slug,
                Portfolio.profile_id != except_profile_id,
            )
        )

        return result.first() is not None

    async def list_projects(self, profile_id: UUID) -> list[PortfolioProject]:
        result = await self.db.execute(
            select(PortfolioProject)
            .where(PortfolioProject.profile_id == profile_id)
            .order_by(
                PortfolioProject.position.asc(),
                PortfolioProject.created_at.asc(),
            )
        )

        return list(result.scalars().all())

    async def get_project(
        self,
        project_id: UUID,
        profile_id: UUID,
    ) -> PortfolioProject | None:
        result = await self.db.execute(
            select(PortfolioProject).where(
                PortfolioProject.id == project_id,
                PortfolioProject.profile_id == profile_id,
            )
        )

        return result.scalar_one_or_none()

    async def count_projects(self, profile_id: UUID) -> int:
        return len(await self.list_projects(profile_id))

    async def add_project(self, project: PortfolioProject) -> PortfolioProject:
        self.db.add(project)
        await self.db.flush()

        return project

    async def delete_project(self, project: PortfolioProject) -> None:
        await self.db.delete(project)
        await self.db.flush()

    async def owned_project_unit(
        self,
        unit_id: UUID,
        profile_id: UUID,
    ):
        """(unit, task) for a project lesson the profile owns, else None."""
        result = await self.db.execute(
            select(TaskLearningUnit, RoadmapTask)
            .join(RoadmapTask, TaskLearningUnit.task_id == RoadmapTask.id)
            .join(RoadmapPhase, RoadmapTask.phase_id == RoadmapPhase.id)
            .join(Roadmap, RoadmapPhase.roadmap_id == Roadmap.id)
            .where(
                TaskLearningUnit.id == unit_id,
                TaskLearningUnit.type == "project",
                Roadmap.profile_id == profile_id,
            )
        )

        return result.first()

    async def suggestions(self, profile_id: UUID, limit: int = 20):
        """Completed project lessons not yet in the portfolio."""
        already = exists().where(
            PortfolioProject.profile_id == profile_id,
            PortfolioProject.source_unit_id == TaskLearningUnit.id,
        )

        result = await self.db.execute(
            select(
                TaskLearningUnit.id,
                TaskLearningUnit.title,
                RoadmapTask.title,
            )
            .join(RoadmapTask, TaskLearningUnit.task_id == RoadmapTask.id)
            .join(RoadmapPhase, RoadmapTask.phase_id == RoadmapPhase.id)
            .join(Roadmap, RoadmapPhase.roadmap_id == Roadmap.id)
            .where(
                Roadmap.profile_id == profile_id,
                TaskLearningUnit.type == "project",
                TaskLearningUnit.completed.is_(True),
                ~already,
            )
            .order_by(TaskLearningUnit.updated_at.desc())
            .limit(limit)
        )

        return result.all()

    async def get_public(self, slug: str):
        """(portfolio, profile) for a public portfolio, else None."""
        result = await self.db.execute(
            select(Portfolio, Profile)
            .join(Profile, Profile.id == Portfolio.profile_id)
            .where(Portfolio.slug == slug, Portfolio.is_public.is_(True))
        )

        return result.first()
