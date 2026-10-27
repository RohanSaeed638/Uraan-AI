"""Sends due learning reminders.

Run every 15 minutes from an external scheduler (Railway/Render cron, or
cron/Task Scheduler locally):

    python -m app.workers.send_reminders

Safe to run more often or twice: each reminder is sent at most once per day.
"""
import asyncio
import logging
import selectors
import sys

from app.db.session import SessionLocal
from app.services.email_service import wait_for_pending
from app.services.reminder_service import ReminderService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("send_reminders")


async def main() -> None:
    async with SessionLocal() as db:
        try:
            result = await ReminderService(db).run()
            await wait_for_pending()
        except Exception:
            await db.rollback()
            raise

    logger.info("Reminders done: %s", result)


if __name__ == "__main__":
    # psycopg's async mode cannot use the default Windows event loop.
    asyncio.run(
        main(),
        loop_factory=(
            (lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))
            if sys.platform == "win32"
            else None
        ),
    )
