import logging

from fastapi import HTTPException, status
from supabase_auth.errors import AuthError, AuthRetryableError

from .supabase import supabase

logger = logging.getLogger(__name__)


def verify_token(token: str):
    """The signed-in user for a Supabase access token.

    Raises 401 when the token is malformed, expired or revoked (the person
    must sign in again) and 503 when Supabase itself cannot be reached (a
    retry may work). Never a 500: a bad token is the caller's problem.
    """
    try:
        response = supabase.auth.get_user(token)
    except AuthRetryableError as exc:
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

    return user
