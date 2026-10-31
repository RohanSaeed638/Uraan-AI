"""Background roadmap work: first generation, regeneration and adaptation.

A job runs after the HTTP response, on its own database session. The roadmap
row carries the state (`status`, `generation_error`, `status_before_job`), so
the browser only has to poll `GET /roadmaps/{id}/status`.

If a job fails, nothing the learner had is lost: content is only replaced after
the AI call succeeded, and the roadmap returns to the status it had before.
"""
import logging
from app.core.analytics import track
from app.ai.llm import use_profile
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.roadmap_schedule import normalize
from app.ai.versions import prompt_version
from app.ai.services.roadmap_generator import RoadmapGenerator
from app.db.session import SessionLocal
from app.models.enums import RoadmapStatus
from app.models.profile import Profile
from app.repositories.career_repository import CareerRepository
from app.repositories.roadmap_content_repository import RoadmapContentRepository
from app.repositories.roadmap_repository import RoadmapRepository

logger = logging.getLogger(__name__)

# A job that has shown no sign of life for this long is treated as lost (for
# example the server restarted while it ran).
STALE_AFTER = timedelta(minutes=10)

FAILURE_MESSAGES = {
    "generate": "We could not create your roadmap. Please try again.",
    "regenerate": "We could not rebuild your roadmap. Your current one is unchanged.",
    "adapt": "We could not update your roadmap. Your current one is unchanged.",
}

# Statuses a roadmap can go back to after a failed regeneration / adaptation.
RESTORABLE = {
    RoadmapStatus.ACTIVE.value,
    RoadmapStatus.PAUSED.value,
    RoadmapStatus.ARCHIVED.value,
    RoadmapStatus.COMPLETED.value,
}


def is_stale(roadmap, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    updated = roadmap.updated_at

    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)

    return roadmap.status == RoadmapStatus.GENERATING and now - updated > STALE_AFTER


def revert_after_failure(roadmap, kind: str, message: str | None = None) -> None:
    """Puts a roadmap back after a failed or lost job."""
    before = roadmap.status_before_job

    if kind == "generate" or before not in RESTORABLE:
        roadmap.status = RoadmapStatus.FAILED
    else:
        roadmap.status = RoadmapStatus(before)

    roadmap.generation_error = message or FAILURE_MESSAGES[kind]
    roadmap.status_before_job = None


def _status_after_success(roadmap) -> RoadmapStatus:
    before = roadmap.status_before_job

    # A finished roadmap that gets new tasks has work left again.
    if before in (None, "", RoadmapStatus.COMPLETED.value):
        return RoadmapStatus.ACTIVE

    return RoadmapStatus(before) if before in RESTORABLE else RoadmapStatus.ACTIVE


async def _profile_of(db: AsyncSession, roadmap) -> Profile:
    profile = (
        await db.execute(select(Profile).where(Profile.id == roadmap.profile_id))
    ).scalar_one()
    use_profile(profile.id, profile.language)

    return profile


async def _generate(db, roadmap, contents, generator):
    profile = await _profile_of(db, roadmap)
    career = await CareerRepository(db).get_by_slug(roadmap.career_slug)

    output = await generator.generate(profile, roadmap, career)
    data = normalize(output.model_dump())

    roadmap.title = data["title"][:255]
    roadmap.description = (data.get("description") or "")[:1000]
    roadmap.prompt_version = prompt_version("roadmap")

    await contents.replace_all(roadmap, data)


async def _adapt(db, roadmap, contents, generator, params: dict):
    profile = await _profile_of(db, roadmap)
    career = await CareerRepository(db).get_by_slug(roadmap.career_slug)

    done = [t for p in roadmap.phases for t in p.tasks if t.completed]
    left = [t for p in roadmap.phases for t in p.tasks if not t.completed]

    daily_hours = params.get("daily_hours") or roadmap.daily_hours
    months_left = params.get("months_left") or max(1, roadmap.target_duration)

    output = await generator.adapt(
        profile,
        roadmap,
        completed=[t.title for t in done],
        unfinished=[t.title for t in left],
        daily_hours=daily_hours,
        months_left=months_left,
        reason=params["reason"],
        note=params.get("note"),
        career=career,
    )

    weeks_done = max((t.week or 0 for t in done), default=0)
    data = normalize(output.model_dump(), first_week=weeks_done + 1)

    await contents.replace_unfinished(roadmap, data)

    # target_duration stays "total months", so what is done counts too.
    roadmap.daily_hours = daily_hours
    roadmap.target_duration = max(1, weeks_done // 4) + months_left
    roadmap.prompt_version = prompt_version("roadmap_adapt")


async def run_job(
    roadmap_id,
    kind: str,
    params: dict | None = None,
    *,
    session_factory=SessionLocal,
    generator: RoadmapGenerator | None = None,
) -> None:
    """Runs one job to the end and records the outcome on the roadmap."""
    generator = generator or RoadmapGenerator()
    params = params or {}

    async with session_factory() as db:
        contents = RoadmapContentRepository(db)

        try:
            roadmap = await contents.load(roadmap_id)

            if roadmap is None:
                return

            if kind == "adapt":
                await _adapt(db, roadmap, contents, generator, params)
            else:
                await _generate(db, roadmap, contents, generator)

            new_status = _status_after_success(roadmap)

            if new_status == RoadmapStatus.ACTIVE:
                await RoadmapRepository(db).archive_active_roadmaps(
                    roadmap.profile_id, except_id=roadmap.id
                )

            roadmap.status = new_status
            roadmap.generation_error = None
            roadmap.status_before_job = None
            await db.commit()
            track(roadmap.profile_id, "roadmap_ready", kind=kind, career=roadmap.career_slug)

        except Exception:
            logger.exception("Roadmap %s failed for %s", kind, roadmap_id)
            await db.rollback()

            try:
                roadmap = await contents.load(roadmap_id)

                if roadmap is not None:
                    revert_after_failure(roadmap, kind)
                    await db.commit()
            except Exception:
                logger.exception("Could not record the failure of %s", roadmap_id)
                await db.rollback()
