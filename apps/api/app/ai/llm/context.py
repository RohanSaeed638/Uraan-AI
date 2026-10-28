"""Whose request an AI call belongs to, without passing it through every
generator. A service calls `use_profile(profile.id, profile.language)` once it
has loaded the learner; `complete()` then records it with the call and, for
content the learner reads in the app, asks for their language. Each web request
and each background job runs in its own context, so this never leaks between
learners."""
from contextvars import ContextVar
from uuid import UUID

_profile_id: ContextVar[UUID | None] = ContextVar("ai_profile_id", default=None)
_language: ContextVar[str | None] = ContextVar("ai_language", default=None)


def use_profile(profile_id: UUID | None, language: str | None = None) -> None:
    _profile_id.set(profile_id)
    _language.set(language)


def current_profile() -> UUID | None:
    return _profile_id.get()


def current_language() -> str | None:
    return _language.get()
