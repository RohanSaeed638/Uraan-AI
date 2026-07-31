from uuid import UUID

from app.models.enums import RoadmapStatus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask

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

        if roadmap:
            roadmap.status = status
            await self.db.commit()

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