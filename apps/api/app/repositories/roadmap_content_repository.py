from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.models.roadmap_version import RoadmapVersion
from app.models.user_task_progress import UserTaskProgress

# Versions kept per roadmap; the oldest are dropped past this.
MAX_VERSIONS = 10


def snapshot_of(roadmap: Roadmap) -> dict:
    """The roadmap's phases and tasks as plain data (the shape the AI returns,
    plus `completed`), so a snapshot can be loaded back with `add_content`."""
    return {
        "title": roadmap.title,
        "description": roadmap.description,
        "daily_hours": roadmap.daily_hours,
        "target_duration": roadmap.target_duration,
        "phases": [
            {
                "title": phase.title,
                "description": phase.description,
                "order": phase.order,
                "estimated_weeks": phase.duration_weeks,
                "milestones": list(phase.milestones or []),
                "tasks": [
                    {
                        "title": task.title,
                        "description": task.description,
                        "resource_links": list(task.resource_links or []),
                        "estimated_hours": task.estimated_hours,
                        "week": task.week,
                        "completed": task.completed,
                    }
                    for task in sorted(phase.tasks, key=lambda t: t.order)
                ],
            }
            for phase in sorted(roadmap.phases, key=lambda p: p.order)
        ],
    }


def summarize(snapshot: dict) -> dict:
    tasks = [t for p in snapshot.get("phases", []) for t in p.get("tasks", [])]

    return {
        "phases": len(snapshot.get("phases", [])),
        "tasks": len(tasks),
        "completed": sum(1 for t in tasks if t.get("completed")),
    }


class RoadmapContentRepository:
    """Reads and rewrites a roadmap's phases and tasks, and its versions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---- loading -----------------------------------------------------------

    async def load(self, roadmap_id) -> Roadmap | None:
        return (
            await self.db.execute(
                select(Roadmap)
                .options(
                    selectinload(Roadmap.phases).selectinload(RoadmapPhase.tasks)
                )
                .where(Roadmap.id == roadmap_id)
                .execution_options(populate_existing=True)
            )
        ).scalar_one_or_none()

    # ---- writing content ---------------------------------------------------

    async def add_content(
        self,
        roadmap: Roadmap,
        roadmap_data: dict,
        first_order: int = 1,
    ) -> None:
        """Adds the phases (and their tasks) of `roadmap_data` after the ones
        already there. Does not commit."""
        for offset, phase_data in enumerate(roadmap_data["phases"]):
            phase = RoadmapPhase(
                roadmap_id=roadmap.id,
                title=phase_data["title"],
                description=phase_data.get("description") or "",
                order=first_order + offset,
                duration_weeks=phase_data.get("estimated_weeks", 0) or 0,
                milestones=phase_data.get("milestones") or [],
            )

            self.db.add(phase)
            await self.db.flush()

            for task_index, task_data in enumerate(phase_data["tasks"], start=1):
                self.db.add(
                    RoadmapTask(
                        phase_id=phase.id,
                        title=task_data["title"],
                        description=task_data.get("description"),
                        resource_links=task_data.get("resource_links") or [],
                        estimated_hours=task_data.get("estimated_hours"),
                        week=task_data.get("week"),
                        completed=bool(task_data.get("completed", False)),
                        order=task_index,
                    )
                )

        await self.db.flush()

    async def _delete_tasks(self, task_ids: list) -> None:
        if not task_ids:
            return

        # Progress rows have no database cascade, so remove them first.
        await self.db.execute(
            delete(UserTaskProgress).where(UserTaskProgress.task_id.in_(task_ids))
        )

    async def replace_all(self, roadmap: Roadmap, roadmap_data: dict) -> None:
        """Swaps every phase for the ones in `roadmap_data`. Does not commit."""
        await self._delete_tasks(
            [t.id for p in roadmap.phases for t in p.tasks]
        )

        for phase in list(roadmap.phases):
            await self.db.delete(phase)

        await self.db.flush()
        await self.db.refresh(roadmap, ["phases"])
        await self.add_content(roadmap, roadmap_data)

    async def replace_unfinished(self, roadmap: Roadmap, new_data: dict) -> None:
        """Keeps finished tasks, drops the rest and appends `new_data`'s phases.

        Phases left without any task disappear. Does not commit."""
        stale = [
            t for p in roadmap.phases for t in p.tasks if not t.completed
        ]
        await self._delete_tasks([t.id for t in stale])

        for task in stale:
            await self.db.delete(task)

        await self.db.flush()
        await self.db.refresh(roadmap, ["phases"])

        order = 0

        for phase in sorted(roadmap.phases, key=lambda p: p.order):
            await self.db.refresh(phase, ["tasks"])

            if not phase.tasks:
                await self.db.delete(phase)
                continue

            order += 1
            phase.order = order

        await self.db.flush()
        await self.add_content(roadmap, new_data, first_order=order + 1)

    # ---- versions ----------------------------------------------------------

    async def save_version(self, roadmap: Roadmap, reason: str) -> RoadmapVersion:
        latest = (
            await self.db.execute(
                select(func.max(RoadmapVersion.version_number)).where(
                    RoadmapVersion.roadmap_id == roadmap.id
                )
            )
        ).scalar_one()

        version = RoadmapVersion(
            roadmap_id=roadmap.id,
            version_number=(latest or 0) + 1,
            reason=reason,
            snapshot=snapshot_of(roadmap),
        )
        self.db.add(version)
        await self.db.flush()

        # Keep only the newest MAX_VERSIONS.
        old = (
            await self.db.execute(
                select(RoadmapVersion.id)
                .where(RoadmapVersion.roadmap_id == roadmap.id)
                .order_by(RoadmapVersion.version_number.desc())
                .offset(MAX_VERSIONS)
            )
        ).scalars().all()

        if old:
            await self.db.execute(
                delete(RoadmapVersion).where(RoadmapVersion.id.in_(old))
            )

        return version

    async def list_versions(self, roadmap_id) -> list[RoadmapVersion]:
        return list(
            (
                await self.db.execute(
                    select(RoadmapVersion)
                    .where(RoadmapVersion.roadmap_id == roadmap_id)
                    .order_by(RoadmapVersion.version_number.desc())
                )
            ).scalars()
        )

    async def get_version(self, roadmap_id, version_id) -> RoadmapVersion | None:
        return (
            await self.db.execute(
                select(RoadmapVersion).where(
                    RoadmapVersion.id == version_id,
                    RoadmapVersion.roadmap_id == roadmap_id,
                )
            )
        ).scalar_one_or_none()
