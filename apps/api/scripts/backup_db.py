"""Writes a compressed copy of the database with pg_dump.

    python scripts/backup_db.py               # backups/uraan-YYYYMMDD-HHMMSS.dump
    python scripts/backup_db.py --keep 14     # and delete all but the newest 14

Needs the PostgreSQL client tools (`pg_dump`) on the PATH. See
docs/runbooks/backup-and-restore.md for restoring.
"""
import argparse
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import settings  # noqa: E402


def plain_url(url: str) -> str:
    """SQLAlchemy writes postgresql+psycopg://; pg_dump wants postgresql://."""
    return url.replace("postgresql+psycopg://", "postgresql://", 1).replace("postgresql+asyncpg://", "postgresql://", 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(ROOT / "backups"), help="folder for the dump")
    parser.add_argument("--keep", type=int, default=0, help="keep only this many newest dumps (0 keeps all)")
    args = parser.parse_args()

    if shutil.which("pg_dump") is None:
        print("pg_dump was not found. Install the PostgreSQL client tools and try again.", file=sys.stderr)
        return 2

    folder = Path(args.out)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"uraan-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.dump"

    # --no-owner / --no-privileges: the dump restores into any project, whoever owns it.
    result = subprocess.run(
        ["pg_dump", "--format=custom", "--no-owner", "--no-privileges", "--file", str(target), plain_url(settings.DATABASE_URL)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        target.unlink(missing_ok=True)
        # The message can include the host but never the password (pg_dump does not echo it).
        print(f"pg_dump failed:\n{result.stderr.strip()}", file=sys.stderr)
        return 1

    print(f"Wrote {target} ({target.stat().st_size / 1_000_000:.1f} MB)")

    if args.keep > 0:
        for old in sorted(folder.glob("uraan-*.dump"))[: -args.keep]:
            old.unlink()
            print(f"Removed {old.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
