import logging

from fastapi import Request
from fastapi.exception_handlers import http_exception_handler as default_http_handler
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.error_codes import error_code

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """The usual `{"detail": ...}` body, plus an `error_code` for the web app to
    translate (see app/core/error_codes.py). Status and headers are unchanged."""
    response = await default_http_handler(request, exc)

    if isinstance(exc.detail, str) and exc.detail:
        import json

        body = json.loads(response.body)
        body["error_code"] = error_code(exc.detail)

        return JSONResponse(body, status_code=exc.status_code, headers=exc.headers)

    return response


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

    response = JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Something went wrong on our side. Please try again.",
            "error_code": "SYSTEM_001",
        },
    )

    origin = request.headers.get("origin")

    if origin and origin in settings.cors_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Vary"] = "Origin"

    return response
