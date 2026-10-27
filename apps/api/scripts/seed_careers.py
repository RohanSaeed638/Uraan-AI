"""Loads data/careers.json into the database (safe to run repeatedly).

    python scripts/seed_careers.py              # insert / update careers
    python scripts/seed_careers.py --check-urls # only test every resource link
"""
import asyncio
import selectors
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.career_catalog import load_catalog  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.services.career_seed import seed_careers, seed_library  # noqa: E402

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; UraanLinkCheck/1.0)"}


async def check_urls() -> int:
    urls = {
        r["url"]: career["slug"]
        for career in load_catalog()
        for r in career["resources"]
    }
    bad = 0

    async with httpx.AsyncClient(
        follow_redirects=True, timeout=45, headers=HEADERS
    ) as client:
        for url, slug in urls.items():
            try:
                response = await client.get(url)
                # 403/429 mean the site blocks scripts, not that the page is gone.
                ok = response.status_code < 400 or response.status_code in (403, 429)
                note = response.status_code
            except httpx.HTTPError as exc:
                ok, note = False, type(exc).__name__

            bad += not ok
            print(f"{'ok ' if ok else 'BAD'} {note} {slug}: {url}")

    print(f"\n{len(urls) - bad}/{len(urls)} links reachable")
    return 1 if bad else 0


async def main() -> int:
    if "--check-urls" in sys.argv:
        return await check_urls()

    async with SessionLocal() as db:
        try:
            result = await seed_careers(db, load_catalog())
            library = await seed_library(db, load_catalog())
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    print("Careers seeded:", result)
    print("Resource library seeded:", library)
    return 0


if __name__ == "__main__":
    sys.exit(
        asyncio.run(
            main(),
            loop_factory=(
                (lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))
                if sys.platform == "win32"
                else None
            ),
        )
    )
