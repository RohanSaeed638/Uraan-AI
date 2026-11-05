"""The platform around the features: request ids, one error shape, health checks,
the /api/v1 prefix and the list queries."""
import asyncio
import json
import logging
import selectors

import httpx
import pytest

from app.core.exceptions import CATEGORY_CODES, category_code, error_body
from app.core.observability import JsonFormatter, request_id_var
from app.main import app


def call(method, url, **kwargs):
    async def go():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as client:
            return await client.request(method, url, **kwargs)

    return asyncio.run(go(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))


# ---- request ids ----------------------------------------------------------------------------------------------------------


def test_every_response_has_a_request_id():
    response = call("GET", "/health")

    assert len(response.headers["x-request-id"]) >= 16


def test_a_caller_supplied_id_is_kept():
    assert call("GET", "/health", headers={"X-Request-ID": "web-abc12345"}).headers["x-request-id"] == "web-abc12345"


@pytest.mark.parametrize("bad", ["short", "has spaces in it!!", "x" * 200, "<script>alert(1)</script>"])
def test_an_unsafe_id_is_replaced(bad):
    got = call("GET", "/health", headers={"X-Request-ID": bad.replace("\n", "")}).headers["x-request-id"]

    assert got != bad and got.isalnum()


def test_errors_carry_the_same_id_in_the_body_and_the_header():
    response = call("GET", "/api/v1/profile/me", headers={"X-Request-ID": "trace-12345678"})
    body = response.json()

    assert response.status_code in (401, 403)
    assert body["request_id"] == "trace-12345678" == response.headers["x-request-id"]
    assert body["code"] in {"AUTH_001", "AUTH_002"} and body["message"] and "detail" in body


def test_ids_do_not_leak_between_requests():
    first = call("GET", "/health").headers["x-request-id"]
    second = call("GET", "/health").headers["x-request-id"]

    assert first != second and request_id_var.get() is None


# ---- one error shape ------------------------------------------------------------------------------------------------------


def test_every_error_status_has_a_stable_code():
    assert category_code(401) == "AUTH_001" and category_code(404) == "NOT_FOUND_001"
    assert category_code(429) == "RATE_LIMIT_001" and category_code(500) == "SYSTEM_001"
    assert category_code(418) == "CLIENT_001" and category_code(504) == "SYSTEM_001"
    assert len(set(CATEGORY_CODES.values())) == len(CATEGORY_CODES)


def test_the_error_body_has_all_the_standard_fields():
    body = error_body(409, "Already finished.")

    assert set(body) == {"detail", "message", "code", "error_code", "request_id"}
    assert body["code"] == "CONFLICT_001" and body["error_code"] == "already_finished"


def test_a_request_the_server_cannot_read_is_a_422_in_the_same_shape():
    response = call("POST", "/api/v1/email/unsubscribe")  # the token is missing

    body = response.json()

    assert response.status_code == 422
    assert body["code"] == "VALIDATION_001" and body["message"] == "The request was not valid."
    assert isinstance(body["detail"], list) and body["detail"][0]["loc"][-1] == "token"


def test_unknown_addresses_are_a_404_in_the_same_shape():
    body = call("GET", "/api/v1/nothing-here").json()

    assert body["code"] == "NOT_FOUND_001" and "request_id" in body


# ---- the version prefix and health ------------------------------------------------------------------------------


def test_everything_is_under_api_v1_except_health():
    paths = set(app.openapi()["paths"])

    assert {p for p in paths if not p.startswith("/api/v1")} == {"/", "/health", "/health/ready"}
    assert "/api/v1/roadmaps" in paths and "/api/v1/admin/stats" in paths


def test_the_old_unprefixed_addresses_are_gone():
    assert call("GET", "/roadmaps").status_code == 404
    assert call("GET", "/careers").status_code == 404
    assert call("GET", "/api/v1/careers").status_code == 200  # public


def test_health_is_cheap_and_ready_checks_the_database():
    assert call("GET", "/health").json() == {"status": "healthy"}

    ready = call("GET", "/health/ready")

    assert ready.status_code == 200 and ready.json() == {"status": "ready", "database": "ok"}


def test_ready_says_503_when_the_database_is_down(monkeypatch):
    import app.main as main

    class Broken:
        async def __aenter__(self):
            raise OSError("no database")

        async def __aexit__(self, *args):
            return False

    monkeypatch.setattr(main, "SessionLocal", lambda: Broken())

    response = call("GET", "/health/ready")

    assert response.status_code == 503 and response.json() == {"status": "unavailable", "database": "error"}


# ---- logs ----------------------------------------------------------------------------------------------------------------------


def test_json_logs_are_one_object_per_line_with_the_request_id():
    token = request_id_var.set("req-12345678")

    try:
        record = logging.LogRecord("uraan.access", logging.INFO, "f.py", 1, "GET %s %d", ("/x", 200), None)
        record.fields = {"status": 200, "ms": 12}
        line = JsonFormatter().format(record)
    finally:
        request_id_var.reset(token)

    data = json.loads(line)

    assert "\n" not in line
    assert data["msg"] == "GET /x 200" and data["request_id"] == "req-12345678"
    assert data["status"] == 200 and data["ms"] == 12 and data["level"] == "INFO"


def test_json_logs_keep_non_ascii_and_exceptions():
    try:
        raise ValueError("پوری بات")
    except ValueError:
        import sys

        record = logging.LogRecord("x", logging.ERROR, "f.py", 1, "failed: کوئی خرابی", (), sys.exc_info())

    data = json.loads(JsonFormatter().format(record))

    assert "کوئی خرابی" in data["msg"] and "ValueError" in data["exc"]
