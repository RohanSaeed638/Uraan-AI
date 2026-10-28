"""Signed links for emails: a learner can unsubscribe with one click, without
signing in, and nobody else can unsubscribe them. The token is the profile id
and its purpose, signed with a key derived from the server secret."""
import base64
import hashlib
import hmac
from uuid import UUID

from app.core.config import settings

PURPOSE_UNSUBSCRIBE = "unsubscribe"


def _key() -> bytes:
    return hashlib.sha256(f"uraan-email:{settings.SUPABASE_JWT_SECRET}".encode()).digest()


def _sign(body: str) -> str:
    digest = hmac.new(_key(), body.encode(), hashlib.sha256).digest()

    return base64.urlsafe_b64encode(digest[:18]).decode().rstrip("=")


def make_token(profile_id: UUID, purpose: str = PURPOSE_UNSUBSCRIBE) -> str:
    body = f"{purpose}:{profile_id}"
    encoded = base64.urlsafe_b64encode(body.encode()).decode().rstrip("=")

    return f"{encoded}.{_sign(body)}"


def read_token(token: str, purpose: str = PURPOSE_UNSUBSCRIBE) -> UUID | None:
    """The profile id inside a valid token, or None for anything else."""
    try:
        encoded, signature = token.split(".", 1)
        body = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)).decode()
        wanted, profile_id = body.split(":", 1)

        if wanted != purpose or not hmac.compare_digest(signature, _sign(body)):
            return None

        return UUID(profile_id)
    except (ValueError, UnicodeDecodeError):
        return None
