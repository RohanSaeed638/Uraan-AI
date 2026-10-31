"""AI-drafts the Urdu (`ur`) and Roman Urdu (`ur-Latn`) message files from the
English ones, for a native speaker to review before launch.

    python scripts/translate_messages.py                 # only what is missing
    python scripts/translate_messages.py --force         # redo everything
    python scripts/translate_messages.py --only ur-Latn  # one language

Reads apps/web/messages/en.json and messages/gamified/en.json; writes ur.json,
ur-Latn.json and gamified/ur*.json beside them. Existing translations are kept
(so a reviewer's edits are never overwritten) unless --force is given.

Each result is checked: the placeholders ({name}), plural forms and tags must
match the English, otherwise that string is retried and finally left in English
(which the app shows as a fallback) and reported.
"""
import argparse
import asyncio
import json
import logging
import re
import selectors
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.ai.llm import AIUnavailableError, complete_text  # noqa: E402

MESSAGES = ROOT.parent / "web" / "messages"
BATCH = 40
SKIP_PREFIXES = ("admin.",)

GLOSSARY = """
Keep these exactly as written, in Latin letters, in every language: Uraan AI, XP, AI, GitHub, YouTube,
LinkedIn, Google, PDF, JSON, README, URL, .ics, Pro, AM, PM, and code, commands, file names and
technology names (Python, JavaScript, React, SQL...).
Never change placeholders such as {name} or {count}, ICU plural syntax such as
{count, plural, one {# day} other {# days}}, or tags such as <b>...</b> and <link>...</link>:
translate only the words around and inside them. Keep emoji and punctuation like "…" and "·".
Keep the length close to the English: these are buttons and labels in a compact interface.
"""

LANGUAGES = {
    "ur": {
        "name": "Urdu",
        "style": (
            "Write in Urdu script, as modern Pakistani Urdu a student would read: clear, polite, "
            "friendly, using \"آپ\". Use the common Urdu-script spelling of widely used English "
            "loanwords instead of formal Urdu coinages. Glossary: roadmap=روڈ میپ, lesson=سبق, "
            "task=ٹاسک, project=پروجیکٹ, mentor=مینٹر, quiz=کوئز, resume=ریزیومے, portfolio=پورٹ فولیو, "
            "streak=مسلسل دن, level=لیول, achievement=کامیابی, leaderboard=لیڈر بورڈ, interview=انٹرویو, "
            "dashboard=ڈیش بورڈ, settings=ترتیبات, profile=پروفائل, calendar=کیلنڈر, planner=پلانر, "
            "notification=اطلاع, mission=مشن, quest=کوئسٹ."
        ),
    },
    "ur-Latn": {
        "name": "Roman Urdu",
        "style": (
            "Write Urdu in the Latin alphabet (Roman Urdu), the way people text in Pakistan: simple, "
            "friendly, using \"aap\". Use the usual informal spellings (hai, hain, karein, aap, ka/ki/ke, "
            "mein, nahin). Keep common English words as they are (roadmap, task, project, quiz, resume, "
            "portfolio, streak, level, dashboard, settings, profile, calendar, planner, mentor, "
            "interview, leaderboard); translate everything else (lesson=sabaq, achievement=kamyabi)."
        ),
    },
}


def flatten(node, prefix=""):
    for key, value in node.items():
        path = f"{prefix}{key}"

        if isinstance(value, dict):
            yield from flatten(value, path + ".")
        else:
            yield path, value


def put(tree: dict, path: str, value: str):
    parts = path.split(".")

    for part in parts[:-1]:
        tree = tree.setdefault(part, {})

    tree[parts[-1]] = value


TOKENS = re.compile(r"\{\w+\}|</?\w+>")
PLURAL = re.compile(r"\{(\w+), (?:plural|select),(?:[^{}]|\{[^{}]*\})*\}")


def signature(text: str) -> list[str]:
    """The placeholders and tags of a message. A plural counts as its variable;
    its branches are translated, so they are not compared."""
    return sorted(TOKENS.findall(PLURAL.sub(lambda m: "{" + m.group(1) + "}", text)))


def valid(english: str, translated: str) -> bool:
    if not translated or not translated.strip():
        return False

    return signature(english) == signature(translated) and english.count("<") == translated.count("<")


async def ask(language: str, batch: dict[str, str]) -> dict[str, str]:
    spec = LANGUAGES[language]
    prompt = f"""Translate these user-interface strings of a career-learning web app for learners in Pakistan
from English into {spec['name']}.

{spec['style']}

{GLOSSARY}

Return ONLY a JSON object with exactly the same keys, each value the translation.

{json.dumps(batch, ensure_ascii=False, indent=1)}"""

    raw = await complete_text(
        [
            {"role": "system", "content": "You are a careful professional translator and localisation expert."},
            {"role": "user", "content": prompt},
        ],
        purpose="translate",
        temperature=0.2,
        max_tokens=4500,
        json_mode=True,
    )

    return json.loads(raw)


CONCURRENCY = 4


async def translate_chunk(language: str, chunk: dict[str, str], gate: asyncio.Semaphore):
    """One batch, retried for the strings that come back unusable."""
    done: dict[str, str] = {}
    pending = chunk

    async with gate:
        for _ in range(3):
            try:
                answer = await ask(language, pending)
            except (AIUnavailableError, json.JSONDecodeError) as error:
                print(f"  batch failed ({error}); retrying")
                continue

            bad = {}

            for key, english in pending.items():
                translated = answer.get(key)

                if isinstance(translated, str) and valid(english, translated):
                    done[key] = translated.strip()
                else:
                    bad[key] = english

            pending = bad

            if not pending:
                break

    return done, list(pending)


async def translate(language: str, source: dict[str, str], existing: dict[str, str], force: bool):
    todo = {k: v for k, v in source.items() if force or k not in existing}
    done: dict[str, str] = {} if force else dict(existing)
    failed: list[str] = []
    keys = list(todo)
    gate = asyncio.Semaphore(CONCURRENCY)
    chunks = [{k: todo[k] for k in keys[start : start + BATCH]} for start in range(0, len(keys), BATCH)]
    finished = 0

    async def run(chunk):
        nonlocal finished
        result = await translate_chunk(language, chunk, gate)
        finished += len(chunk)
        print(f"  {language}: {finished}/{len(keys)}")

        return result

    for translated, left in await asyncio.gather(*(run(chunk) for chunk in chunks)):
        done.update(translated)
        failed.extend(left)

    return done, failed


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save(path: Path, flat: dict[str, str], order: list[str]):
    tree: dict = {}

    for key in order:
        if key in flat:
            put(tree, key, flat[key])

    path.write_text(json.dumps(tree, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


async def main():
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="translate everything again")
    parser.add_argument("--only", choices=list(LANGUAGES), help="one language")
    args = parser.parse_args()

    jobs = [
        (MESSAGES / "en.json", MESSAGES / "{lang}.json"),
        (MESSAGES / "gamified" / "en.json", MESSAGES / "gamified" / "{lang}.json"),
    ]

    for language in [args.only] if args.only else list(LANGUAGES):
        for source_path, target_pattern in jobs:
            target = Path(str(target_pattern).format(lang=language))
            # The admin portal is for staff and stays in English.
            source = {k: v for k, v in flatten(load(source_path)) if not k.startswith(SKIP_PREFIXES)}
            existing = dict(flatten(load(target)))

            print(f"{target.relative_to(MESSAGES.parent)}: {len(source)} strings")

            done, failed = await translate(language, source, existing, args.force)

            save(target, done, list(source))

            if failed:
                print(f"  left in English ({len(failed)}): {failed[:10]}")


if __name__ == "__main__":
    asyncio.run(main(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))
