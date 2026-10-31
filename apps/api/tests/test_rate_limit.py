"""Rate limits: who is counted, what is exempt, and what a refusal looks like."""
import asyncio
import base64
import json
import selectors
from types import SimpleNamespace

import httpx
import pytest
from fastapi import Depends, FastAPI

from app.core import rate_limit
from app.core.config import settings
from app.core.exceptions import http_exception_handler
from app.core.observability import RequestContextMiddleware
from app.core.rate_limit import (
    RateLimiter,
    RateLimitMiddleware,
    daily_limit,
    token_subject,
)
from starlette.exceptions import HTTPException as StarletteHTTPException


def run(coro):
    return asyncio.run(coro, loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))


def bearer(sub: str) -> str:
    def part(data):
        return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")

    return f"Bearer {part({'alg': 'none'})}.{part({'sub': sub})}.signature"


@pytest.fixture(autouse=True)
def limits_on(monkeypatch):
    """A fresh counter store, the limits switched on and small."""
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(settings, "RATE_LIMIT_ANONYMOUS", "3/hour")
    monkeypatch.setattr(settings, "RATE_LIMIT_AUTHENTICATED", "5/hour")
    monkeypatch.setattr(settings, "RATE_LIMIT_ADDRESS", "8/hour")
    monkeypatch.setattr(settings, "RATE_LIMIT_AI_CHAT", "2/day")
    monkeypatch.setattr(rate_limit, "_limiter", RateLimiter("memory://"))


def make_app(user=None):
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    @app.get("/things")
    def things():
        return {"ok": True}

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/api/v1/calendar/feed/abc.ics")
    def feed():
        return {"ok": True}

    @app.get("/api/v1/portfolio/public/someone")
    def portfolio():
        return {"ok": True}

    async def who():
        return user or SimpleNamespace(id="learner-1")

    from app.api.dependencies import get_current_user

    app.dependency_overrides[get_current_user] = who

    @app.post("/chat", dependencies=[Depends(daily_limit("ai-chat", "RATE_LIMIT_AI_CHAT"))])
    def chat():
        return {"ok": True}

    return app


def get(app, path="/things", method="GET", headers=None, client=("1.2.3.4", 5000)):
    async def go():
        transport = httpx.ASGITransport(app=app, client=client)

        async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
            return await c.request(method, path, headers=headers or {})

    return run(go())


# ---- the general limit ---------------------------------------------------------------------------------------------


def test_someone_not_signed_in_gets_the_small_limit():
    app = make_app()

    assert [get(app).status_code for _ in range(4)] == [200, 200, 200, 429]


def test_a_signed_in_learner_gets_the_bigger_limit():
    app = make_app()
    headers = {"Authorization": bearer("learner-1")}

    assert [get(app, headers=headers).status_code for _ in range(6)] == [200] * 5 + [429]


def test_each_learner_is_counted_on_their_own():
    app = make_app()

    for _ in range(5):
        get(app, headers={"Authorization": bearer("busy")})

    assert get(app, headers={"Authorization": bearer("busy")}).status_code == 429
    assert get(app, headers={"Authorization": bearer("calm")}).status_code == 200


def test_anonymous_visitors_are_counted_per_address():
    app = make_app()

    for _ in range(3):
        get(app, client=("9.9.9.9", 1))

    assert get(app, client=("9.9.9.9", 1)).status_code == 429
    assert get(app, client=("8.8.8.8", 1)).status_code == 200


def test_inventing_accounts_does_not_get_around_the_address_cap():
    app = make_app()
    statuses = [get(app, headers={"Authorization": bearer(f"made-up-{i}")}).status_code for i in range(10)]

    assert statuses[:8] == [200] * 8 and statuses[8:] == [429, 429]


def test_the_refusal_is_a_429_in_the_standard_shape_with_retry_after():
    app = make_app()

    for _ in range(3):
        get(app)

    response = get(app, headers={"X-Request-ID": "trace-12345678"})
    body = response.json()

    assert response.status_code == 429
    assert body["code"] == "RATE_LIMIT_001" and body["message"].startswith("Too many requests")
    assert body["detail"] == body["message"] and body["request_id"] == "trace-12345678"
    assert body["retry_after"] >= 1
    assert int(response.headers["retry-after"]) == body["retry_after"]


def test_responses_say_how_much_is_left():
    app = make_app()
    first = get(app)
    second = get(app)

    assert first.headers["x-ratelimit-limit"] == "3" and first.headers["x-ratelimit-remaining"] == "2"
    assert second.headers["x-ratelimit-remaining"] == "1"


@pytest.mark.parametrize("path", ["/health", "/api/v1/calendar/feed/abc.ics", "/api/v1/portfolio/public/someone"])
def test_health_and_token_links_are_never_limited(path):
    app = make_app()

    assert {get(app, path).status_code for _ in range(20)} == {200}


def test_browser_preflight_requests_are_not_counted():
    app = make_app()

    for _ in range(10):
        get(app, method="OPTIONS")

    assert get(app).status_code == 200


def test_the_switch_turns_it_all_off(monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", False)
    app = make_app()

    assert {get(app).status_code for _ in range(10)} == {200}


# ---- daily limits on the AI features ---------------------------------------------------------------------------


def test_the_daily_ai_limit_counts_per_learner():
    app = make_app()
    first = [get(app, "/chat", "POST", {"Authorization": bearer("a")}).status_code for _ in range(3)]

    assert first == [200, 200, 429]

    other = make_app(SimpleNamespace(id="learner-2"))

    assert get(other, "/chat", "POST", {"Authorization": bearer("b")}).status_code == 200


def test_the_daily_refusal_says_to_try_tomorrow():
    app = make_app()

    for _ in range(2):
        get(app, "/chat", "POST", {"Authorization": bearer("a")})

    response = get(app, "/chat", "POST", {"Authorization": bearer("a")})
    body = response.json()

    assert response.status_code == 429 and "tomorrow" in body["message"]
    assert body["code"] == "RATE_LIMIT_001" and int(response.headers["retry-after"]) > 60


# ---- the machinery -----------------------------------------------------------------------------------------------------


def test_the_subject_is_read_from_a_bearer_token():
    assert token_subject(bearer("abc-123")) == "abc-123"


@pytest.mark.parametrize(
    "header",
    [None, "", "Basic abc", "Bearer", "Bearer one-part", "Bearer a.b.c", "Bearer a.%%%.c", "Bearer a." + "e30" + ".c"],
)
def test_anything_else_has_no_subject(header):
    assert token_subject(header) is None


def test_a_broken_counter_store_lets_requests_through():
    class Broken:
        async def hit(self, *args, **kwargs):
            raise ConnectionError("redis is down")

        async def get_window_stats(self, *args, **kwargs):
            raise ConnectionError("redis is down")

    limiter = RateLimiter("memory://")
    limiter.strategy = Broken()

    assert run(limiter.hit("3/hour", "x")) == (True, 1, 0)


def test_the_moving_window_frees_a_slot_as_time_passes(monkeypatch):
    limiter = RateLimiter("memory://")
    results = [run(limiter.hit("2/second", "w")) for _ in range(3)]

    assert [r[0] for r in results] == [True, True, False]
    assert results[2][2] >= 1


def test_a_redis_address_is_read_as_the_async_client():
    pytest.importorskip("redis")

    limiter = RateLimiter("redis://localhost:6379")

    assert type(limiter.storage).__name__ == "RedisStorage"
