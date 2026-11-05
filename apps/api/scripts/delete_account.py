"""Deletes one learner and all their data, when they have asked for it.

    python scripts/delete_account.py --email someone@example.com           # shows what WOULD go, changes nothing
    python scripts/delete_account.py --email someone@example.com --yes     # really deletes

Take a backup first if in doubt (docs/runbooks/backup-and-restore.md), and check
you are talking to the account's owner before running it with --yes. The Privacy
Policy promises these requests are done within 30 days.
"""
import argparse
import asyncio
import selectors
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.services.account_deletion import delete_learner  # noqa: E402


async def main(email: str, really: bool) -> int:
    engine = create_async_engine(settings.DATABASE_URL)

    try:
        async with engine.connect() as conn:
            transaction = await conn.begin()
            row = (
                await conn.execute(text("select id from auth.users where lower(email) = lower(:email)"), {"email": email})
            ).first()

            if row is None:
                print(f"No account with the address {email}.")
                await transaction.rollback()
                return 1

            deleted = await delete_learner(conn, row.id)

            print(("Deleted" if really else "Would delete") + f" for {email}:")
            for table, count in sorted(deleted.items(), key=lambda item: -item[1]):
                print(f"  {count:>6}  {table}")

            if really:
                await transaction.commit()
                print("Done.")
            else:
                await transaction.rollback()
                print("Nothing was changed. Run again with --yes to delete.")
    finally:
        await engine.dispose()

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--email", required=True)
    parser.add_argument("--yes", action="store_true", help="really delete (otherwise only shows what would go)")
    args = parser.parse_args()

    sys.exit(
        asyncio.run(
            main(args.email, args.yes),
            loop_factory=(lambda: asyncio.SelectorEventLoop(selectors.SelectSelector())) if sys.platform == "win32" else None,
        )
    )
