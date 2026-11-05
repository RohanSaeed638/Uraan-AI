"""Product analytics (PostHog) for the numbers the SRS tracks: sign-up and
onboarding, roadmaps built, lessons and tasks done, quizzes, interviews, mentor
use, documents, portfolios, achievements.

Events are sent from the server, where they are certain to have happened, and
only carry the learner's profile id (no name, email or text). It does nothing
unless POSTHOG_API_KEY is set, and a failure here never reaches the learner:
the SDK sends from a background thread.
"""
import logging
from uuid import UUID

from app.core.config import settings

logger = logging.getLogger(__name__)

_client = None
_started = False


def _posthog():
    global _client, _started

    if _started:
        return _client

    _started = True

    if not settings.POSTHOG_API_KEY:
        return None

    try:
        from posthog import Posthog

        _client = Posthog(settings.POSTHOG_API_KEY, host=settings.POSTHOG_HOST, disable_geoip=True)
    except Exception:
        logger.exception("PostHog could not start; analytics are off")

    return _client


def track(profile_id: UUID | str | None, event: str, **properties) -> None:
    """Records one event for a learner. Never raises."""
    client = _posthog()

    if client is None or profile_id is None:
        return

    try:
        client.capture(event, distinct_id=str(profile_id), properties={"env": settings.APP_ENV, **properties})
    except Exception:
        logger.exception("Could not record the %s event", event)


def flush() -> None:
    """For jobs that exit right after: sends what is queued."""
    if _client is not None:
        try:
            _client.flush()
        except Exception:
            logger.exception("Could not flush analytics")


def reset_for_tests() -> None:
    global _client, _started

    _client, _started = None, False
