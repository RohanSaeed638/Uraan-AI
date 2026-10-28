from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.career import Career, CareerResource, CareerSkill

CAREER_FIELDS = (
    "name", "category", "icon", "color", "description", "difficulty",
    "estimated_months", "salary_min_pkr", "salary_max_pkr", "market_demand",
)


async def seed_careers(db: AsyncSession, catalog: list[dict]) -> dict:
    """Inserts or updates every career in the catalogue, by slug.

    Skills and resources are replaced to match the file. Careers that are not
    in the file are left alone. The caller commits.
    """
    created = updated = 0

    for entry in catalog:
        career = (
            await db.execute(select(Career).where(Career.slug == entry["slug"]))
        ).scalar_one_or_none()

        if career is None:
            career = Career(slug=entry["slug"])
            db.add(career)
            created += 1
        else:
            updated += 1

        for field in CAREER_FIELDS:
            setattr(career, field, entry[field])

        career.is_active = True
        career.skills = [
            CareerSkill(name=name, order_number=i)
            for i, name in enumerate(entry["skills"], start=1)
        ]
        career.resources = [
            CareerResource(
                title=r["title"],
                type=r["type"],
                provider=r.get("provider"),
                url=r["url"],
                is_free=r.get("is_free", True),
                difficulty=r.get("difficulty"),
                order_number=i,
            )
            for i, r in enumerate(entry["resources"], start=1)
        ]

    await db.flush()

    return {"created": created, "updated": updated}


async def seed_library(db: AsyncSession, catalog: list[dict]) -> dict:
    """Fills the resource library from the catalogue's career resources.

    One library row per URL; `career_slugs` lists every career that uses it.
    Existing rows keep their ratings and bookmarks. The caller commits."""
    from app.models.library import LibraryResource

    by_url: dict[str, dict] = {}

    for career in catalog:
        for r in career["resources"]:
            entry = by_url.setdefault(r["url"], {**r, "career_slugs": []})

            if career["slug"] not in entry["career_slugs"]:
                entry["career_slugs"].append(career["slug"])

    created = updated = 0
    existing = {
        row.url: row
        for row in (await db.execute(select(LibraryResource))).scalars()
    }

    for url, entry in by_url.items():
        row = existing.get(url)

        if row is None:
            row = LibraryResource(url=url)
            db.add(row)
            created += 1
        else:
            updated += 1

        row.title = entry["title"]
        row.type = entry["type"]
        row.provider = entry.get("provider")
        row.is_free = entry.get("is_free", True)
        row.difficulty = entry.get("difficulty")
        row.career_slugs = entry["career_slugs"]

    await db.flush()

    return {"created": created, "updated": updated}
