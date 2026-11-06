"""Weekly: re-checks the learning links and takes dead ones out.

    python -m app.workers.check_links

Run it about once a week from the same scheduler as the reminders. It checks the resource library and
every link in learners' roadmaps that has not been checked for a week, removes dead links from tasks
(a task left with none gets a search for its topic), and switches off library resources that have
been dead on two checks in a row. Safe to run more often: recent results are reused.
"""
import asyncio
import logging
import selectors
import sys

from app.db.session import SessionLocal
from app.services.link_service import sweep

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("check_links")


async def main() -> None:
    async with SessionLocal() as db:
        try:
            result = await sweep(db)
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    logger.info("Link check done: %s", result)


if __name__ == "__main__":
    # psycopg's async mode cannot use the default Windows event loop.
    asyncio.run(
        main(),
        loop_factory=(
            (lambda: asyncio.SelectorEventLoop(selectors.SelectSelector())) if sys.platform == "win32" else None
        ),
    )
