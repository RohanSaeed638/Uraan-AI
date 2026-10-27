"""The learner's language: which values are accepted, and which AI calls ask for it."""
import asyncio

import pytest
from pydantic import ValidationError

from app.ai import llm
from app.ai.llm import use_profile
from app.ai.llm.router import LLMRouter
from app.ai.llm.types import LLMResult
from app.ai.prompts.language import (
    SUPPORTED,
    generation_rule,
    language_name,
    reply_rule,
)
from app.schemas.profile import PatchProfileRequest


def test_three_languages_are_supported():
    assert SUPPORTED == ("en", "ur", "ur-Latn")


def test_profile_accepts_all_three_and_rejects_others():
    for code in SUPPORTED:
        assert PatchProfileRequest(language=code).language == code

    with pytest.raises(ValidationError):
        PatchProfileRequest(language="fr")


def test_english_adds_nothing_to_generated_content():
    assert generation_rule("en") == ""
    assert generation_rule(None) == ""
    assert generation_rule("klingon") == ""


def test_urdu_and_roman_urdu_are_told_apart():
    assert "Urdu script" in generation_rule("ur")
    assert "Latin" in generation_rule("ur-Latn")
    assert "Roman Urdu" in reply_rule("ur-Latn")
    assert (language_name("ur"), language_name("ur-Latn"), language_name("en")) == (
        "Urdu",
        "Roman Urdu",
        "English",
    )


class Capture:
    name, model = "capture", "m"

    def __init__(self):
        self.seen = []

    async def complete(self, request):
        self.seen.append([m["content"] for m in request.messages if m["role"] == "system"])

        return LLMResult(text="ok", provider="capture", model="m", latency_ms=1)


def ask(monkeypatch, purpose, language):
    provider = Capture()

    async def recorder(row):
        pass

    monkeypatch.setattr(llm, "get_router", lambda: LLMRouter([provider], recorder=recorder))

    async def scenario():
        use_profile(None, language)
        await llm.complete_text([{"role": "user", "content": "hi"}], purpose=purpose)

    asyncio.run(scenario())

    return provider.seen[0]


@pytest.mark.parametrize("purpose", ["roadmap", "roadmap_adapt", "lessons", "quiz", "career", "review"])
def test_content_the_learner_reads_is_asked_for_in_their_language(monkeypatch, purpose):
    systems = ask(monkeypatch, purpose, "ur")

    assert len(systems) == 1 and "Urdu script" in systems[0]


@pytest.mark.parametrize("purpose", ["mentor", "motivation", "planner", "document", "portfolio", "interview"])
def test_other_calls_are_left_alone(monkeypatch, purpose):
    assert ask(monkeypatch, purpose, "ur") == []


def test_english_learners_get_no_extra_message(monkeypatch):
    assert ask(monkeypatch, "roadmap", "en") == []
    assert ask(monkeypatch, "roadmap", None) == []


# ---- messages the server writes ------------------------------------------------------------------


def test_every_language_has_every_message_with_the_same_placeholders():
    import string

    from app.core.texts import _TEXTS

    def fields(template):
        return {name for _, name, _, _ in string.Formatter().parse(template) if name}

    english = _TEXTS["en"]

    for language in ("ur", "ur-Latn"):
        assert set(_TEXTS[language]) == set(english), language

        for key, template in english.items():
            assert fields(_TEXTS[language][key]) == fields(template), (language, key)


def test_text_falls_back_to_english():
    from app.core.texts import text

    assert text("daily_start_title", "klingon") == "Time to study"
    assert text("daily_start_title", None) == "Time to study"
    assert text("daily_start_title", "ur") != "Time to study"


def test_reminders_follow_the_learners_language():
    from datetime import datetime

    from app.services.reminder_service import daily_message, weekly_message

    local = datetime(2026, 11, 2, 18, 0)  # a Monday

    assert daily_message(5, False, local, "ur-Latn").title == "Apni 5 din ki streak barqarar rakhein"
    assert daily_message(5, False, local).title == "Keep your 5-day streak alive"
    assert "XP" in weekly_message(40, local, "ur").body


def test_the_dashboard_fallback_line_follows_the_language():
    from app.services.motivation_service import fallback_message

    assert fallback_message({"streak_days": 3}, "en").startswith("3 days in a row")
    assert fallback_message({"streak_days": 3}, "ur-Latn").startswith("3 din musalsal")


def test_dates_inside_messages():
    from datetime import date

    from app.core.texts import short_date

    assert short_date(date(2026, 11, 3)) == "Nov 3"
    assert short_date(date(2026, 11, 3), "ur-Latn") == "Nov 3"
    assert short_date(date(2026, 11, 3), "ur") == "3 نومبر"
