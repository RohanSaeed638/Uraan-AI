"""Copies the careers catalogue text (names, descriptions, categories, skills) from
data/careers.json into the web app's English messages, under `catalog`, so it
can be translated like the rest of the interface. Run from apps/api:

    python scripts/sync_career_messages.py
    python scripts/translate_messages.py     # drafts ur / ur-Latn

The web app falls back to the catalogue's own English text when a translation
is missing, so a career added to the file never shows blank.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EN = ROOT.parent / "web" / "messages" / "en.json"
CATALOGUE = ROOT / "data" / "careers.json"


def key(text: str) -> str:
    """The same rule as `catalogKey` in apps/web/lib/career-text.ts."""
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:80].rstrip("_")


def main():
    careers = json.loads(CATALOGUE.read_text(encoding="utf-8"))["careers"]
    messages = json.loads(EN.read_text(encoding="utf-8"))
    catalog = {"careers": {}, "categories": {}, "skills": {}}

    for career in careers:
        catalog["careers"][career["slug"]] = {
            "name": career["name"],
            "description": career["description"],
        }

        if career.get("category"):
            catalog["categories"][key(career["category"])] = career["category"]

        for skill in career.get("skills", []):
            catalog["skills"][key(skill)] = skill

    messages["catalog"] = catalog
    EN.write_text(json.dumps(messages, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"{len(catalog['careers'])} careers, {len(catalog['categories'])} categories, "
        f"{len(catalog['skills'])} skills"
    )


if __name__ == "__main__":
    sys.exit(main())
