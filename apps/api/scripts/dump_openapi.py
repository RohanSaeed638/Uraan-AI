"""Writes the API's OpenAPI description to apps/api/openapi.json.

    python scripts/dump_openapi.py

The web app turns it into TypeScript types (`npm run gen:api` in apps/web), so
a change to an endpoint shows up as a type error in the web code. CI re-runs
both steps and fails if the committed files are out of date.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.main import app  # noqa: E402

target = ROOT / "openapi.json"
target.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"wrote {target}")
