"""Error tracking (Sentry). Off until SENTRY_DSN is set.

What is sent is kept small on purpose: the error, where it happened, the
request id and the learner's profile id. Not headers, cookies, bodies, names or
emails: those can hold tokens and personal text."""
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

_SENSITIVE = {"authorization", "cookie", "set-cookie", "x-api-key", "apikey"}


def scrub(event: dict, hint: dict | None = None) -> dict | None:
    """Removes request headers, cookies, bodies and query strings before sending."""
    request = event.get("request")

    if isinstance(request, dict):
        headers = request.get("headers")

        if isinstance(headers, dict):
            request["headers"] = {k: v for k, v in headers.items() if k.lower() not in _SENSITIVE}

        for key in ("cookies", "data", "query_string"):
            request.pop(key, None)

    # Never identify a learner by anything but the profile id.
    user = event.get("user")

    if isinstance(user, dict):
        event["user"] = {"id": user["id"]} if "id" in user else {}

    return event


def init_sentry() -> bool:
    if not settings.SENTRY_DSN:
        return False

    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.APP_ENV,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            send_default_pii=False,
            before_send=scrub,
        )

        return True
    except Exception:
        logger.exception("Sentry could not start; errors will only be logged")

        return False


def tag_request(request_id: str) -> None:
    """Puts the request id on whatever error follows, so a report and a log line meet."""
    try:
        import sentry_sdk

        sentry_sdk.set_tag("request_id", request_id)
    except Exception:
        pass


def identify(profile_or_auth_id) -> None:
    try:
        import sentry_sdk

        sentry_sdk.set_user({"id": str(profile_or_auth_id)})
    except Exception:
        pass


def report(exc: BaseException) -> None:
    try:
        import sentry_sdk

        if sentry_sdk.is_initialized():
            sentry_sdk.capture_exception(exc)
    except Exception:
        pass
