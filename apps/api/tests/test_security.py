import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, Request
from supabase_auth.errors import AuthApiError, AuthRetryableError

from app.core import security
from app.core.exceptions import global_exception_handler


class _Auth:
    def __init__(self, result=None, error=None):
        self.result, self.error = result, error

    def get_user(self, token):
        if self.error:
            raise self.error
        return self.result


def _use(monkeypatch, auth):
    monkeypatch.setattr(security, "supabase", SimpleNamespace(auth=auth))


def test_valid_token_returns_the_user(monkeypatch):
    user = SimpleNamespace(id="u1", email="a@b.c")
    _use(monkeypatch, _Auth(result=SimpleNamespace(user=user)))

    assert security.verify_token("good") is user


@pytest.mark.parametrize(
    "error",
    [
        AuthApiError("invalid JWT", 401, "bad_jwt"),
        AuthApiError("token expired", 403, "session_expired"),
    ],
)
def test_bad_or_expired_token_is_401_not_500(monkeypatch, error):
    _use(monkeypatch, _Auth(error=error))

    with pytest.raises(HTTPException) as exc:
        security.verify_token("bad")

    assert exc.value.status_code == 401
    assert exc.value.headers["WWW-Authenticate"] == "Bearer"


def test_missing_user_is_401(monkeypatch):
    _use(monkeypatch, _Auth(result=SimpleNamespace(user=None)))

    with pytest.raises(HTTPException) as exc:
        security.verify_token("x")

    assert exc.value.status_code == 401


@pytest.mark.parametrize("error", [AuthRetryableError("down", 0), ConnectionError("boom")])
def test_supabase_outage_is_503(monkeypatch, error):
    _use(monkeypatch, _Auth(error=error))

    with pytest.raises(HTTPException) as exc:
        security.verify_token("x")

    assert exc.value.status_code == 503


def _request(origin=None):
    headers = [(b"origin", origin.encode())] if origin else []
    return Request(
        {"type": "http", "method": "GET", "path": "/x", "headers": headers, "query_string": b""}
    )


def test_unhandled_errors_do_not_leak_details():
    response = asyncio.run(
        global_exception_handler(_request(), RuntimeError("password=hunter2 at C:/secret/path"))
    )

    body = response.body.decode()

    assert response.status_code == 500
    assert "hunter2" not in body and "secret" not in body
    assert "SYSTEM_001" in body


def test_error_response_keeps_cors_for_allowed_origin_only():
    allowed = asyncio.run(
        global_exception_handler(_request("http://localhost:3000"), RuntimeError("x"))
    )
    other = asyncio.run(
        global_exception_handler(_request("http://evil.example"), RuntimeError("x"))
    )

    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-origin" not in other.headers
