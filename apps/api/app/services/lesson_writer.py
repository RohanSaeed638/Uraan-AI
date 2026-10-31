"""Writes the lesson text behind a saved plan.

`ensure_plan` saves the outline in seconds with every reading, project and
exercise marked `pending`; this fills them in, the first day's first, each one
saved as soon as it is done so the learner's page fills in as they watch. It is
safe to run twice: a lesson is claimed with a single UPDATE before it is
written, and a claim that was never finished (the server restarted) is taken
over after a few minutes.
"""
import asyncio
import logging
from uuid import UUID

from sqlalchemy import select, text, update

from app.ai.llm import use_profile
from app.ai.schemas.learning_plan_schema import PlanUnit
from app.ai.services.learning_unit_generator import LearningUnitGenerator
from app.core.analytics import track
from app.db.session import SessionLocal
from app.models.profile import Profile
from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.models.task_learning_unit import TaskLearningUnit

logger = logging.getLogger(__name__)

PARALLEL_WRITERS = 4
STALE_MINUTES = 5

CLAIM = text(
    "update task_learning_units set status = 'writing', updated_at = now() "
    "where id = :id and (status = 'pending' or "
    "(status = 'writing' and updated_at < now() - make_interval(mins => :stale))) "
    "returning id"
)


def plan_of(row: TaskLearningUnit) -> PlanUnit:
    """The outline saved with the lesson, or a bare one for finished lessons
    (the writer only needs their title and day to list them as siblings)."""
    saved = (row.details or {}).get("_plan")

    if saved:
        return PlanUnit(**saved)

    return PlanUnit(
        day=row.day,
        order=row.order,
        type=row.type.value if hasattr(row.type, "value") else row.type,
        title=row.title,
        description=row.description or "",
        estimated_minutes=row.estimated_minutes or 20,
    )


async def write_pending_lessons(task_id: UUID, generator=None, session_factory=SessionLocal) -> dict:
    """Fills in every lesson of the task that is waiting. Returns how many were
    written and how many failed; never raises (it runs in the background)."""
    generator = generator or LearningUnitGenerator()
    counts = {"written": 0, "failed": 0}

    try:
        async with session_factory() as db:
            task = (await db.execute(select(RoadmapTask).where(RoadmapTask.id == task_id))).scalar_one_or_none()

            if task is None:
                return counts

            roadmap = (
                await db.execute(
                    select(Roadmap).join(RoadmapPhase, RoadmapPhase.roadmap_id == Roadmap.id).where(
                        RoadmapPhase.id == task.phase_id
                    )
                )
            ).scalar_one()
            profile = (await db.execute(select(Profile).where(Profile.id == roadmap.profile_id))).scalar_one()
            rows = list(
                (
                    await db.execute(
                        select(TaskLearningUnit)
                        .where(TaskLearningUnit.task_id == task_id)
                        .order_by(TaskLearningUnit.day, TaskLearningUnit.order)
                    )
                ).scalars()
            )

            plans = {row.id: plan_of(row) for row in rows}
            waiting = [row.id for row in rows if row.status in ("pending", "writing")]
            profile_id, language = profile.id, profile.language

        use_profile(profile_id, language)
        gate = asyncio.Semaphore(PARALLEL_WRITERS)
        everything = list(plans.values())

        async def write_one(unit_id: UUID):
            async with gate:
                async with session_factory() as db:
                    claimed = (await db.execute(CLAIM, {"id": unit_id, "stale": STALE_MINUTES})).first()
                    await db.commit()

                    if claimed is None:
                        return  # another writer has it, or it is already done

                unit = plans[unit_id]

                try:
                    content, details = await generator.write_unit(unit, everything, roadmap, task)
                    new_status = "ready"
                except Exception:
                    logger.exception("Could not write lesson %s of task %s", unit_id, task_id)
                    content, details, new_status = None, None, "failed"

                async with session_factory() as db:
                    values = {"status": new_status}

                    if new_status == "ready":
                        values.update(content=content, details=details)

                    await db.execute(update(TaskLearningUnit).where(TaskLearningUnit.id == unit_id).values(**values))
                    await db.commit()

                counts["written" if new_status == "ready" else "failed"] += 1

        await asyncio.gather(*(write_one(unit_id) for unit_id in waiting))

        if counts["written"]:
            track(profile_id, "lessons_written", count=counts["written"], failed=counts["failed"])
    except Exception:
        logger.exception("Writing the lessons of task %s failed", task_id)

    return counts


def needs_writer(units) -> bool:
    """Is anything waiting to be written, or claimed so long ago that the writer must have died?"""
    from datetime import datetime, timedelta, timezone

    stale = datetime.now(timezone.utc) - timedelta(minutes=STALE_MINUTES)

    return any(
        u.status == "pending" or (u.status == "writing" and u.updated_at is not None and u.updated_at < stale)
        for u in units
    )


async def requeue_failed(db, task_id: UUID) -> int:
    """Failed lessons go back to waiting, so a retry writes them again."""
    result = await db.execute(
        update(TaskLearningUnit)
        .where(TaskLearningUnit.task_id == task_id, TaskLearningUnit.status == "failed")
        .values(status="pending")
    )

    return result.rowcount or 0
