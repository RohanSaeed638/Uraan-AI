import hashlib
import logging
import time

from fastapi import HTTPException, status
from supabase_auth.errors import AuthError, AuthRetryableError

from .config import settings
from .supabase import supabase

logger = logging.getLogger(__name__)

# Asking Supabase who a token belongs to is a network round trip (most of a request's
# time), so a verified token is remembered briefly. A sign-out or revoked session is
# noticed within AUTH_CACHE_SECONDS; failures are never remembered.
_verified: dict[str, tuple[float, object]] = {}
_MAX_REMEMBERED = 2000


def _remembered(key: str):
    hit = _verified.get(key)

    if hit and hit[0] > time.monotonic():
        return hit[1]

    _verified.pop(key, None)
    return None


def _remember(key: str, user) -> None:
    if len(_verified) >= _MAX_REMEMBERED:
        now = time.monotonic()

        for stale in [k for k, (until, _) in _verified.items() if until <= now]:
            del _verified[stale]

        if len(_verified) >= _MAX_REMEMBERED:
            _verified.clear()

    _verified[key] = (time.monotonic() + settings.AUTH_CACHE_SECONDS, user)


def verify_token(token: str):
    """The signed-in user for a Supabase access token.

    Raises 401 when the token is malformed, expired or revoked (the person
    must sign in again) and 503 when Supabase itself cannot be reached (a
    retry may work). Never a 500: a bad token is the caller's problem.
    """
    key = hashlib.sha256(token.encode()).hexdigest()

    if settings.AUTH_CACHE_SECONDS > 0 and (known := _remembered(key)) is not None:
        return known

    response = None

    # Supabase is across the network and now and then drops a connection: try
    # once more before telling the person the service is unavailable.
    for attempt in (1, 2):
        try:
            response = supabase.auth.get_user(token)
            break
        except AuthRetryableError as exc:
            if attempt == 2:
                logger.warning("Supabase unreachable while verifying a token: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="The sign-in service is unavailable. Please try again shortly.",
                ) from exc
        except AuthError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session. Please sign in again.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        except Exception as exc:  # network errors from the HTTP client
            if attempt == 2:
                logger.exception("Unexpected error while verifying a token")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="The sign-in service is unavailable. Please try again shortly.",
                ) from exc

    user = getattr(response, "user", None)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if settings.AUTH_CACHE_SECONDS > 0:
        _remember(key, user)

    return user
