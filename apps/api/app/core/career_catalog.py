"""The curated career catalogue file (data/careers.json).

The file is the source of truth: `scripts/seed_careers.py` copies it into the
database and the profile validation reads its slugs, so the two cannot drift.
"""
import json
from functools import lru_cache
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parents[2] / "data" / "careers.json"


@lru_cache
def load_catalog() -> list[dict]:
    with CATALOG_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)["careers"]


def catalog_slugs() -> set[str]:
    return {career["slug"] for career in load_catalog()}


# Careers whose daily work involves writing code or commands: only these get
# coding exercises in their lessons.
CODING_CATEGORIES = {"Software", "Data and AI", "Security and Infrastructure"}


def is_coding_career(slug: str | None) -> bool:
    for career in load_catalog():
        if career["slug"] == slug:
            return career.get("category") in CODING_CATEGORIES

    return False
