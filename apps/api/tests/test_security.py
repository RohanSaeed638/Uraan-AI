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


class _Flaky:
    """Fails the first `failures` calls with `error`, then answers."""

    def __init__(self, failures, error, result):
        self.calls, self.failures, self.error, self.result = 0, failures, error, result

    def get_user(self, token):
        self.calls += 1

        if self.calls <= self.failures:
            raise self.error

        return self.result


@pytest.mark.parametrize("error", [AuthRetryableError("dropped", 0), ConnectionError("Server disconnected")])
def test_one_dropped_connection_to_supabase_is_retried(monkeypatch, error):
    user = SimpleNamespace(id="u1", email="a@b.c")
    auth = _Flaky(1, error, SimpleNamespace(user=user))
    _use(monkeypatch, auth)

    assert security.verify_token("good") is user
    assert auth.calls == 2


def test_two_dropped_connections_in_a_row_are_a_503(monkeypatch):
    auth = _Flaky(5, ConnectionError("down"), None)
    _use(monkeypatch, auth)

    with pytest.raises(HTTPException) as exc:
        security.verify_token("x")

    assert exc.value.status_code == 503 and auth.calls == 2


def test_a_bad_token_is_not_retried(monkeypatch):
    auth = _Flaky(5, AuthApiError("invalid JWT", 401, "bad_jwt"), None)
    _use(monkeypatch, auth)

    with pytest.raises(HTTPException) as exc:
        security.verify_token("bad")

    assert exc.value.status_code == 401 and auth.calls == 1


# ---- remembering a verified token ---------------------------------------------------------------------------------------


class _Counting(_Auth):
    calls = 0

    def get_user(self, token):
        _Counting.calls += 1
        return super().get_user(token)


@pytest.fixture
def remembering(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "AUTH_CACHE_SECONDS", 60)
    monkeypatch.setattr(security, "_verified", {})
    _Counting.calls = 0


def test_a_verified_token_is_not_checked_with_supabase_again(monkeypatch, remembering):
    user = SimpleNamespace(id="u1")
    _use(monkeypatch, _Counting(result=SimpleNamespace(user=user)))

    assert security.verify_token("good") is user and security.verify_token("good") is user
    assert _Counting.calls == 1


def test_a_remembered_token_expires(monkeypatch, remembering):
    _use(monkeypatch, _Counting(result=SimpleNamespace(user=SimpleNamespace(id="u1"))))
    clock = [1000.0]
    monkeypatch.setattr(security.time, "monotonic", lambda: clock[0])

    security.verify_token("good")
    clock[0] += 61
    security.verify_token("good")

    assert _Counting.calls == 2


def test_failed_checks_are_never_remembered(monkeypatch, remembering):
    _use(monkeypatch, _Counting(error=AuthApiError("bad", 401, "bad_jwt")))

    for _ in range(2):
        with pytest.raises(HTTPException):
            security.verify_token("bad")

    assert _Counting.calls == 2


def test_each_token_is_remembered_on_its_own(monkeypatch, remembering):
    _use(monkeypatch, _Counting(result=SimpleNamespace(user=SimpleNamespace(id="u1"))))

    security.verify_token("one")
    security.verify_token("two")

    assert _Counting.calls == 2


def test_asking_for_the_current_roadmap_before_having_one_is_a_404_not_a_crash():
    import asyncio

    from app.services.roadmap_service import RoadmapService

    class Profiles:
        async def get_by_auth_user_id(self, _):
            return SimpleNamespace(id="p1")

    class Roadmaps:
        async def get_latest(self, _):
            return None

    service = RoadmapService.__new__(RoadmapService)
    service.profile_repository, service.roadmap_repository = Profiles(), Roadmaps()

    with pytest.raises(HTTPException) as caught:
        asyncio.run(service.get_current("u1"))

    assert caught.value.status_code == 404
