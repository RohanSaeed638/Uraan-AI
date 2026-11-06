"""Keeps learners' resource links working: records what the checker finds and takes dead links out."""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.link_check import LinkCheck
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.services import link_checker
from app.services.link_checker import DEAD, LinkResult, fallback_link, is_search_link

logger = logging.getLogger(__name__)

# A result this young is trusted without asking the website again.
FRESH_FOR = timedelta(days=7)


async def known_results(db: AsyncSession, urls: list[str]) -> dict[str, LinkCheck]:
    if not urls:
        return {}

    # populate_existing: results are written with plain SQL, so rows already held by this session are stale.
    rows = (
        await db.execute(select(LinkCheck).where(LinkCheck.url.in_(urls)).execution_options(populate_existing=True))
    ).scalars().all()

    return {row.url: row for row in rows}


async def record(db: AsyncSession, results: dict[str, LinkResult]) -> None:
    """Saves what was found, and counts how many checks in a row found each address dead."""
    for url, result in results.items():
        statement = insert(LinkCheck).values(
            url=url, status=result.status, http_status=result.http_status, reason=result.reason[:120],
            fail_count=1 if result.status == DEAD else 0,
        )
        await db.execute(
            statement.on_conflict_do_update(
                index_elements=["url"],
                set_={
                    "status": statement.excluded.status,
                    "http_status": statement.excluded.http_status,
                    "reason": statement.excluded.reason,
                    "checked_at": datetime.now(timezone.utc),
                    "fail_count": (
                        LinkCheck.fail_count + 1 if result.status == DEAD else 0
                    ),
                },
            )
        )


async def dead_among(db: AsyncSession, urls: list[str], checker=link_checker.check_many) -> set[str]:
    """Which of these addresses are dead: recent results are reused, the rest are checked now."""
    urls = [u for u in dict.fromkeys(urls) if u and not is_search_link(u)]
    known = await known_results(db, urls)
    cutoff = datetime.now(timezone.utc) - FRESH_FOR
    stale = [u for u in urls if u not in known or known[u].checked_at < cutoff]

    if stale:
        fresh = await checker(stale)
        await record(db, fresh)
    else:
        fresh = {}

    def status_of(url: str) -> str | None:
        if url in fresh:
            return fresh[url].status

        return known[url].status if url in known else None

    return {u for u in urls if status_of(u) == DEAD}


async def repair_tasks(db: AsyncSession, tasks: list[RoadmapTask], checker=link_checker.check_many) -> dict:
    """Takes dead links out of these tasks. A task left with no link gets a search for its topic instead,
    so there is always somewhere to go. Returns {checked, removed, tasks_changed}."""
    urls = [url for task in tasks for url in (task.resource_links or [])]
    dead = await dead_among(db, urls, checker)
    changed = removed = 0

    for task in tasks:
        links = list(task.resource_links or [])
        kept = [url for url in links if url not in dead]

        if len(kept) == len(links):
            continue

        removed += len(links) - len(kept)
        changed += 1
        # Assigned afresh so the database sees the list changed.
        task.resource_links = kept or [fallback_link(task.title)]

    return {"checked": len(set(urls)), "removed": removed, "tasks_changed": changed}


async def repair_roadmap_links(roadmap_id, session_factory=SessionLocal, checker=link_checker.check_many) -> dict | None:
    """Run after a roadmap is built or rebuilt. Never raises and never delays the learner: the roadmap
    is already usable, this only tidies its links a moment later."""
    if not settings.LINK_CHECK_ENABLED:
        return None

    try:
        async with session_factory() as db:
            tasks = (
                await db.execute(
                    select(RoadmapTask)
                    .join(RoadmapPhase, RoadmapPhase.id == RoadmapTask.phase_id)
                    .where(RoadmapPhase.roadmap_id == roadmap_id)
                )
            ).scalars().all()
            summary = await repair_tasks(db, list(tasks), checker)
            await db.commit()

            if summary["removed"]:
                logger.info("Roadmap %s: removed %s dead link(s)", roadmap_id, summary["removed"])

            return summary
    except Exception:
        logger.exception("Could not check the links of roadmap %s", roadmap_id)

        return None


# ---- the weekly sweep ---------------------------------------------------------------------------------------------------

LIBRARY_DEACTIVATE_AFTER = 2  # checks in a row


async def sweep(db: AsyncSession, limit: int = 400, checker=link_checker.check_many) -> dict:
    """Weekly job: re-checks the resource library and every learner's links that are due, takes dead
    links out of tasks, and switches off library resources that stay dead."""
    cutoff = datetime.now(timezone.utc) - FRESH_FOR

    library = (await db.execute(text("select id, url from library_resources where is_active"))).all()
    task_urls = (
        await db.execute(
            text(
                "select distinct unnest(resource_links) as url from roadmap_tasks "
                "where resource_links is not null"
            )
        )
    ).scalars().all()

    wanted = list(dict.fromkeys([u for _, u in library] + list(task_urls)))
    wanted = [u for u in wanted if u and not is_search_link(u)]
    known = await known_results(db, wanted)
    due = [u for u in wanted if u not in known or known[u].checked_at < cutoff][:limit]

    if due:
        await record(db, await checker(due))
        await db.flush()

    known = await known_results(db, wanted)
    dead_tasks = {u for u in task_urls if u in known and known[u].status == DEAD}
    removed = changed = 0

    if dead_tasks:
        tasks = (
            await db.execute(select(RoadmapTask).where(RoadmapTask.resource_links.overlap(list(dead_tasks))))
        ).scalars().all()

        for task in tasks:
            summary = await repair_tasks(db, [task], checker=_nothing_to_check)
            removed += summary["removed"]
            changed += summary["tasks_changed"]

    switched_off = 0

    for resource_id, url in library:
        entry = known.get(url)

        if entry and entry.status == DEAD and entry.fail_count >= LIBRARY_DEACTIVATE_AFTER:
            await db.execute(text("update library_resources set is_active = false where id = :i"), {"i": resource_id})
            switched_off += 1

    return {
        "checked": len(due),
        "dead_links_removed": removed,
        "tasks_changed": changed,
        "library_switched_off": switched_off,
    }


async def _nothing_to_check(urls: list[str]) -> dict[str, LinkResult]:
    """The sweep already checked everything; this stops `repair_tasks` asking a second time."""
    return {}
