"""Adds every fixed API message to the web app's English message file, under
`errors.<code>`, so it can be translated. Run from apps/api:

    python scripts/sync_error_messages.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.error_codes import fixed_messages  # noqa: E402

EN = ROOT.parent / "web" / "messages" / "en.json"


def main():
    messages = json.loads(EN.read_text(encoding="utf-8"))
    errors = messages.setdefault("errors", {})
    added = 0

    for code, text in fixed_messages(ROOT / "app").items():
        if errors.get(code) != text:
            added += code not in errors
            errors[code] = text

    EN.write_text(json.dumps(messages, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{added} new, {len(errors)} total")


if __name__ == "__main__":
    main()
