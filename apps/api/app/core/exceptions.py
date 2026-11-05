import logging

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.error_codes import error_code
from app.core.monitoring import report
from app.core.observability import current_request_id

logger = logging.getLogger(__name__)


# One stable code per kind of failure, for clients that branch on it and for
# support ("AUTH_001"). `error_code` is separate: it is the message as words and
# is what the web app translates (see app/core/error_codes.py).
CATEGORY_CODES = {
    400: "REQUEST_001",
    401: "AUTH_001",
    403: "AUTH_002",
    404: "NOT_FOUND_001",
    409: "CONFLICT_001",
    422: "VALIDATION_001",
    429: "RATE_LIMIT_001",
    500: "SYSTEM_001",
    502: "UPSTREAM_001",
    503: "UPSTREAM_002",
}


def category_code(status_code: int) -> str:
    if status_code in CATEGORY_CODES:
        return CATEGORY_CODES[status_code]

    return "CLIENT_001" if status_code < 500 else "SYSTEM_001"


def error_body(status_code: int, message: str, detail=None, **extra) -> dict:
    """The one shape every error response has:
    {"detail", "message", "code", "error_code", "request_id", ...}"""
    return {
        "detail": message if detail is None else detail,
        "message": message,
        "code": category_code(status_code),
        "error_code": error_code(message),
        "request_id": current_request_id(),
        **extra,
    }


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """The usual `{"detail": ...}` body, in the standard error shape. Status and
    headers are unchanged."""
    message = exc.detail if isinstance(exc.detail, str) and exc.detail else "The request could not be completed."

    return JSONResponse(
        error_body(exc.status_code, message, detail=exc.detail if exc.detail else message),
        status_code=exc.status_code,
        headers=exc.headers,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """FastAPI's list of field errors stays in `detail` (the web app reads it);
    the standard fields are added around it."""
    return JSONResponse(
        error_body(422, "The request was not valid.", detail=jsonable_encoder(exc.errors())),
        status_code=422,
    )


async def global_exception_handler(request: Request, exc: Exception):
    """Last resort for errors nobody handled.

    The details go to the log; the client only gets a generic message, so
    internal text (SQL, file paths, library errors) is never exposed.

    This handler runs outside the CORS middleware, so a plain response would
    reach the browser without CORS headers and look like a "CORS error". The
    allowed origin is added here to keep the real status readable.
    """
    logger.error(
        "Unhandled error on %s %s",
        request.method,
        request.url.path,
        exc_info=exc,
    )

    report(exc)

    response = JSONResponse(
        status_code=500,
        content={
            "success": False,
            **error_body(500, "Something went wrong on our side. Please try again."),
        },
    )

    origin = request.headers.get("origin")

    if origin and origin in settings.cors_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Vary"] = "Origin"

    return response
