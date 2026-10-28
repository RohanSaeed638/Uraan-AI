"""Stable codes for the messages the API shows people.

The API writes its messages in English. Every error response also carries an
`error_code` made from that message, and the web app looks the code up in its
message files (`errors.<code>` in apps/web/messages/*.json) to show the learner
their own language. Anything without a translation falls back to the English
text, so a new message never shows up blank.

The code is the message as lowercase words joined by underscores, so it needs no
registry to maintain; `tests/test_error_codes.py` checks that the web app has a
translation entry for every fixed message in this package.
"""
import ast
import re
from pathlib import Path

MAX_LENGTH = 80


def error_code(message: str) -> str:
    """"Profile not found" -> "profile_not_found". The web app uses the same rule."""
    words = re.sub(r"[^a-z0-9]+", "_", message.lower()).strip("_")

    return words[:MAX_LENGTH].rstrip("_")


def fixed_messages(root: Path) -> dict[str, str]:
    """Every message written as plain text in the code, as {code: message}.

    Looks at `detail=` of HTTPException, at `*_FAILED`-style module constants that
    are passed as detail, and at the roadmap job failure messages. Messages built
    with f-strings change at run time and are left out.
    """
    found: dict[str, str] = {}

    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))

        constants: dict[str, str] = {}

        for node in tree.body:
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                constants[node.targets[0].id] = node.value.value

        def text(value: ast.AST) -> str | None:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                return value.value

            if isinstance(value, ast.Name):
                return constants.get(value.id)

            return None

        for node in ast.walk(tree):
            if isinstance(node, ast.keyword) and node.arg == "detail":
                message = text(node.value)

                if message:
                    found[error_code(message)] = message

        for node in tree.body:
            if (
                isinstance(node, ast.Assign)
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "FAILURE_MESSAGES"
                and isinstance(node.value, ast.Dict)
            ):
                for value in node.value.values:
                    message = text(value)

                    if message:
                        found[error_code(message)] = message

    return found
