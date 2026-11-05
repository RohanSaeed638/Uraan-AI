"""Knowing what the API is doing: a request id on every request and log line,
JSON logs for production, and one access line per request with its time.

The id comes from the caller's `X-Request-ID` (so the web app and the API log
the same id for one click) or is made here, and goes back in the response
header and in every error body, so a learner can quote it and we can find the
request."""
import json
import logging
import re
import time
import uuid
from contextvars import ContextVar

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import settings
from app.core.monitoring import tag_request

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

access_log = logging.getLogger("uraan.access")

# A caller-supplied id is kept only if it is a plain short token: it ends up in logs.
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


def current_request_id() -> str | None:
    return request_id_var.get()


class JsonFormatter(logging.Formatter):
    """One JSON object per line: easy for any log service to index."""

    def format(self, record: logging.LogRecord) -> str:
        line = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S") + f".{int(record.msecs):03d}Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": request_id_var.get(),
        }

        # Fields passed with `extra={"fields": {...}}`.
        line.update(getattr(record, "fields", {}) or {})

        if record.exc_info:
            line["exc"] = self.formatException(record.exc_info)

        return json.dumps(line, default=str, ensure_ascii=False)


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get() or "-"

        return True


def configure_logging() -> None:
    """JSON in production, readable text while developing (LOG_FORMAT overrides)."""
    wanted = settings.LOG_FORMAT or ("json" if settings.APP_ENV.lower() in {"production", "prod"} else "text")
    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(
        JsonFormatter()
        if wanted == "json"
        else logging.Formatter("%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s")
    )

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)

    # The database driver logs every statement at INFO when echo is on; keep it off by default.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO if settings.SQL_ECHO else logging.WARNING)
    # Our own access line replaces uvicorn's.
    logging.getLogger("uvicorn.access").disabled = True


class RequestContextMiddleware:
    """Pure ASGI (not BaseHTTPMiddleware) so the request id reaches background work."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {k.decode().lower(): v.decode("latin-1") for k, v in scope["headers"]}
        given = headers.get("x-request-id", "")
        request_id = given if _SAFE_ID.match(given) else uuid.uuid4().hex
        token = request_id_var.set(request_id)
        scope.setdefault("state", {})["request_id"] = request_id
        tag_request(request_id)

        started = time.perf_counter()
        status = {"code": 500}

        async def send_with_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                status["code"] = message["status"]
                message.setdefault("headers", []).append((b"x-request-id", request_id.encode()))

            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            ms = round((time.perf_counter() - started) * 1000)
            path = scope["path"]

            # Health checks every few seconds would drown everything else.
            if path not in {"/health", "/health/ready"}:
                access_log.log(
                    logging.WARNING if ms >= settings.SLOW_REQUEST_MS else logging.INFO,
                    "%s %s %s %dms",
                    scope["method"],
                    path,
                    status["code"],
                    ms,
                    extra={"fields": {"method": scope["method"], "path": path, "status": status["code"], "ms": ms}},
                )

            request_id_var.reset(token)
