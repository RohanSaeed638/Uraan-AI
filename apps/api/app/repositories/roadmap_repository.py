from uuid import UUID

from app.models.enums import RoadmapStatus
from app.schemas import roadmap
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.models.profile import Profile

class RoadmapRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        profile,
        roadmap_data: dict,
    ) -> Roadmap:

        roadmap = Roadmap(
            profile_id=profile.id,
            title=roadmap_data["title"],
            description=roadmap_data.get("description"),
            status="completed",
        )

        self.db.add(roadmap)

        await self.db.flush()

        for phase_index, phase_data in enumerate(
            roadmap_data["phases"],
            start=1,
        ):

            phase = RoadmapPhase(
                roadmap_id=roadmap.id,
                title=phase_data["title"],
                description=phase_data.get("description"),
                order=phase_index,
                duration_weeks=phase_data.get("estimated_weeks", 0)
            )

            self.db.add(phase)

            await self.db.flush()

            for task_index, task_data in enumerate(
                phase_data["tasks"],
                start=1,
            ):

                task = RoadmapTask(
                    phase_id=phase.id,
                    title=task_data["title"],
                    description=task_data.get("description"),
                    resource_links=task_data.get("resource_links", []),
                    estimated_hours=task_data.get(
                        "estimated_hours"
                    ),
                    completed=False,
                    order=task_index,
                )

                self.db.add(task)

        await self.db.commit()

        return await self.get_latest(profile.id)

    async def get_by_profile_id(
        self,
        profile_id: UUID,
    ) -> Roadmap | None:

        result = await self.db.execute(
            select(Roadmap).where(
                Roadmap.profile_id == profile_id
            ).order_by(
                    Roadmap.created_at.desc()
              )
        )

        return result.scalars().first()

    async def update(
        self,
        roadmap: Roadmap,
    ) -> Roadmap:

        await self.db.commit()

        await self.db.refresh(roadmap)

        return roadmap

    async def get_latest(
        self,
        profile_id,
    ):

        result = await self.db.execute(

            select(Roadmap)

            .options(

                selectinload(Roadmap.phases)

                .selectinload(RoadmapPhase.tasks)
                .selectinload(RoadmapTask.learning_units)
            )

            .where(
                Roadmap.profile_id == profile_id
            )

            .order_by(
                Roadmap.created_at.desc()
            )

        )

        return result.scalars().first()
    
    async def get_by_id(  
        self,
        roadmap_id: UUID,
        user_id: UUID,
    ):

        result = await self.db.execute(
            select(Roadmap)
            .options(
            selectinload(Roadmap.phases)
            .selectinload(RoadmapPhase.tasks)
            .selectinload(RoadmapTask.learning_units)
            )
            .where(
                Roadmap.id == roadmap_id,
                Roadmap.profile_id == user_id
            )
        )

        return result.scalar_one_or_none()

    async def update_status(
    self,
    roadmap_id: UUID,
    status: RoadmapStatus,
    ):
        result = await self.db.execute(
                select(Roadmap).where(
                Roadmap.id == roadmap_id
            )
        )

        roadmap = result.scalars().first()

        if not roadmap:
           return None

        roadmap.status = status

        return roadmap

    async def get_all_by_user(
        self,
        user_id: UUID,
    ) -> list[Roadmap]:

        result = await self.db.execute(
            select(Roadmap)
            .where(Roadmap.profile_id == user_id)
            .order_by(Roadmap.updated_at.desc())
        )

        return result.scalars().all()        

    async def get_roadmap_for_progress(
        self,
        db: AsyncSession,
        roadmap_id: UUID,
        user_id: UUID,
    ) -> Roadmap | None:

        stmt = (
            select(Roadmap)
            .where(
                Roadmap.id == roadmap_id,
                Roadmap.user_id == user_id,
            )
            .options(
                selectinload(Roadmap.phases)
                .selectinload(RoadmapPhase.tasks)
                .selectinload(RoadmapTask.learning_units)
            )
        )

        result = await db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_owned_roadmap(
        db: AsyncSession,
        user_id: UUID,
        roadmap_id: UUID,
    ):
        stmt = select(Roadmap).where(
            Roadmap.id == roadmap_id,
            Roadmap.user_id == user_id,
        )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def lock_profile(self, profile_id: UUID) -> None:
        stmt = (
            select(Profile.id)
            .where(Profile.id == profile_id)
            .with_for_update()
        )

        await self.db.execute(stmt)

    async def get_by_id_for_profile(
        self,
        roadmap_id: UUID,
        profile_id: UUID,
    ) -> Roadmap | None:

        stmt = (
            select(Roadmap)
            .where(
                Roadmap.id == roadmap_id,
                Roadmap.profile_id == profile_id,
            )
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()    

    async def archive_active_roadmaps(
        self,
        profile_id: UUID,
    ) -> None:

        stmt = (
            update(Roadmap)
            .where(
                Roadmap.profile_id == profile_id,
                Roadmap.status == RoadmapStatus.ACTIVE,
            )
            .values(status=RoadmapStatus.ARCHIVED)
            .execution_options(synchronize_session="fetch")
        )

        await self.db.execute(stmt)

    async def get_active_for_profile(
        self,
        profile_id: UUID,
    ) -> Roadmap | None:

        stmt = (
            select(Roadmap)
            .where(
                Roadmap.profile_id == profile_id,
                Roadmap.status == RoadmapStatus.ACTIVE,
            )
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()    

    async def delete_roadmap(
        self,
        roadmap: Roadmap,
    ) -> None:
        await self.db.delete(roadmap)
        await self.db.flush()