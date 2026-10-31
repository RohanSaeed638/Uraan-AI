"""Rate limits: the cheap protection against runaway scripts and runaway cost.

Two layers, both on the `limits` library's moving window:

* a **general limit** on every request (middleware): 50 an hour for someone who
  is not signed in (per address), 500 an hour for a signed-in learner (per
  account, plus a roomier cap per address so rotating made-up accounts does not
  help);
* **daily limits on the expensive AI features** (a dependency on those routes):
  100 mentor questions and 10 roadmap builds per learner per day.

Over a limit the answer is 429 in the standard error shape with a `Retry-After`
header. Counters live in memory by default (one process); set
`RATE_LIMIT_STORAGE_URI=redis://...` so several processes share them.
"""
import base64
import json
import logging
import time

from fastapi import Depends, HTTPException
from limits import parse
from limits.aio.storage import MemoryStorage
from limits.aio.strategies import MovingWindowRateLimiter
from limits.storage import storage_from_string
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.exceptions import error_body

logger = logging.getLogger(__name__)

# Open to anyone without a login by design, and not tied to one address: the
# token in the link is the credential (calendar apps and mail scanners poll
# these from shared addresses).
EXEMPT_PREFIXES = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/calendar/feed/",
    "/api/v1/email/unsubscribe",
    "/api/v1/portfolio/public/",
)

GENERAL_MESSAGE = "Too many requests. Please wait a few minutes and try again."
DAILY_MESSAGE = "You have reached today's limit for this. Please try again tomorrow."


class RateLimiter:
    def __init__(self, storage_uri: str = "memory://"):
        # "redis://host" is read as the async client; the `async+` prefix says so.
        uri = storage_uri if storage_uri.startswith(("memory", "async+")) else f"async+{storage_uri}"
        self.storage = MemoryStorage() if uri.startswith("memory") else storage_from_string(uri)
        self.strategy = MovingWindowRateLimiter(self.storage)

    async def hit(self, spec: str, *identifiers: str) -> tuple[bool, int, int]:
        """Counts one request. Returns (allowed, remaining, seconds until a slot frees)."""
        item = parse(spec)

        try:
            allowed = await self.strategy.hit(item, *identifiers)
            stats = await self.strategy.get_window_stats(item, *identifiers)
        except Exception:
            # A broken counter store must not take the whole API down with it.
            logger.exception("Rate limit storage failed; letting the request through")

            return True, 1, 0

        return allowed, stats.remaining, max(1, int(stats.reset_time - time.time()))

    async def reset(self) -> None:
        await self.storage.reset()


_limiter: RateLimiter | None = None


def limiter() -> RateLimiter:
    global _limiter

    if _limiter is None:
        _limiter = RateLimiter(settings.RATE_LIMIT_STORAGE_URI)

    return _limiter


def token_subject(authorization: str | None) -> str | None:
    """The account id inside a bearer token, read without checking it. Only used
    to choose a counter: the token is verified (or refused) by the route itself,
    and made-up ones also count against the address cap."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None

    try:
        payload = authorization.split(".")[1]
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        sub = data.get("sub")

        return sub if isinstance(sub, str) and 0 < len(sub) <= 64 else None
    except (IndexError, ValueError, UnicodeDecodeError):
        return None


def client_address(scope: Scope) -> str:
    client = scope.get("client")

    return client[0] if client else "unknown"


def too_many(status_message: str, retry_after: int) -> JSONResponse:
    return JSONResponse(
        error_body(429, status_message, retry_after=retry_after),
        status_code=429,
        headers={"Retry-After": str(retry_after)},
    )


class RateLimitMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not settings.RATE_LIMIT_ENABLED:
            await self.app(scope, receive, send)
            return

        path = scope["path"]

        if scope["method"] == "OPTIONS" or path == "/" or path.startswith(EXEMPT_PREFIXES):
            await self.app(scope, receive, send)
            return

        headers = {k.decode().lower(): v.decode("latin-1") for k, v in scope["headers"]}
        address = client_address(scope)
        subject = token_subject(headers.get("authorization"))

        if subject is None:
            checks = [(settings.RATE_LIMIT_ANONYMOUS, f"anon:{address}")]
        else:
            checks = [
                (settings.RATE_LIMIT_AUTHENTICATED, f"user:{subject}"),
                (settings.RATE_LIMIT_ADDRESS, f"address:{address}"),
            ]

        shown = None

        for spec, key in checks:
            allowed, remaining, reset = await limiter().hit(spec, "general", key)

            if not allowed:
                response = too_many(GENERAL_MESSAGE, reset)
                await response(scope, receive, send)
                return

            shown = shown or (spec, remaining)

        async def send_with_limits(message):
            if message["type"] == "http.response.start" and shown:
                message.setdefault("headers", []).extend(
                    [
                        (b"x-ratelimit-limit", str(parse(shown[0]).amount).encode()),
                        (b"x-ratelimit-remaining", str(shown[1]).encode()),
                    ]
                )

            await send(message)

        await self.app(scope, receive, send_with_limits)


def daily_limit(feature: str, spec_name: str):
    """A route dependency: `Depends(daily_limit("mentor", "RATE_LIMIT_AI_CHAT"))`.
    Counts per signed-in learner, after their login has been verified."""

    async def check(current_user=Depends(get_current_user)):
        if not settings.RATE_LIMIT_ENABLED:
            return

        allowed, _, reset = await limiter().hit(getattr(settings, spec_name), feature, str(current_user.id))

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=DAILY_MESSAGE,
                headers={"Retry-After": str(reset)},
            )

    return check
