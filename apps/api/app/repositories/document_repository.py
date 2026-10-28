from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.models.task_learning_unit import TaskLearningUnit


class DocumentRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def count(self, profile_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Document)
            .where(Document.profile_id == profile_id)
        )

        return int(result.scalar_one())

    async def create(self, document: Document) -> Document:
        self.db.add(document)
        await self.db.flush()

        return document

    async def list_for_profile(self, profile_id: UUID) -> list[Document]:
        result = await self.db.execute(
            select(Document)
            .where(Document.profile_id == profile_id)
            .order_by(Document.updated_at.desc())
        )

        return list(result.scalars().all())

    async def get_owned(
        self,
        document_id: UUID,
        profile_id: UUID,
    ) -> Document | None:
        result = await self.db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.profile_id == profile_id,
            )
        )

        return result.scalar_one_or_none()

    async def delete(self, document: Document) -> None:
        await self.db.delete(document)
        await self.db.flush()

    async def completed_task_titles(
        self,
        profile_id: UUID,
        limit: int = 30,
    ) -> list[str]:
        result = await self.db.execute(
            select(RoadmapTask.title)
            .join(RoadmapPhase, RoadmapTask.phase_id == RoadmapPhase.id)
            .join(Roadmap, RoadmapPhase.roadmap_id == Roadmap.id)
            .where(
                Roadmap.profile_id == profile_id,
                RoadmapTask.completed.is_(True),
            )
            .order_by(RoadmapTask.updated_at.desc())
            .limit(limit)
        )

        return list(dict.fromkeys(result.scalars().all()))

    async def completed_project_titles(
        self,
        profile_id: UUID,
        limit: int = 15,
    ) -> list[str]:
        result = await self.db.execute(
            select(TaskLearningUnit.title)
            .join(RoadmapTask, TaskLearningUnit.task_id == RoadmapTask.id)
            .join(RoadmapPhase, RoadmapTask.phase_id == RoadmapPhase.id)
            .join(Roadmap, RoadmapPhase.roadmap_id == Roadmap.id)
            .where(
                Roadmap.profile_id == profile_id,
                TaskLearningUnit.type == "project",
                TaskLearningUnit.completed.is_(True),
            )
            .order_by(TaskLearningUnit.updated_at.desc())
            .limit(limit)
        )

        return list(dict.fromkeys(result.scalars().all()))
