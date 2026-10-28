"""The languages a learner can pick, and how each one is asked of the AI.

`en` English, `ur` Urdu in Urdu script, `ur-Latn` Urdu written in the Latin
alphabet ("Roman Urdu", the way most Pakistanis type on a phone)."""

SUPPORTED = ("en", "ur", "ur-Latn")

# Used where a prompt only needs to say how to answer.
LANGUAGES = {
    "en": "Reply in English.",
    "ur": (
        "Reply in Urdu (Urdu script). Keep code, commands and technical terms "
        "in English."
    ),
    "ur-Latn": (
        "Reply in Roman Urdu: Urdu written in the Latin alphabet, the way "
        "people text each other in Pakistan (for example \"Aap ka roadmap tayar "
        "hai\"). Keep code, commands and technical terms in English."
    ),
}

# Added to generation prompts (roadmaps, lessons, quizzes, documents) so the
# learner reads their own language. JSON keys, ids and enum values never change.
_GENERATED = {
    "ur": (
        "- Write every learner-facing text value (titles, descriptions, "
        "explanations, tips, feedback) in Urdu, in Urdu script. Keep code, "
        "commands, URLs, product names and technical terms in English. Do not "
        "translate JSON keys or fixed values such as types and levels."
    ),
    "ur-Latn": (
        "- Write every learner-facing text value (titles, descriptions, "
        "explanations, tips, feedback) in Roman Urdu: Urdu written in the Latin "
        "alphabet, as people text in Pakistan. Keep code, commands, URLs, "
        "product names and technical terms in English. Do not translate JSON "
        "keys or fixed values such as types and levels."
    ),
}


def is_supported(code: str | None) -> bool:
    return code in SUPPORTED


def reply_rule(code: str | None) -> str:
    return LANGUAGES.get(code or "", LANGUAGES["en"])


def generation_rule(code: str | None) -> str:
    """A prompt bullet for generated content; '' for English (the default)."""
    return _GENERATED.get(code or "", "")


def language_name(code: str | None) -> str:
    return {"ur": "Urdu", "ur-Latn": "Roman Urdu"}.get(code or "", "English")
