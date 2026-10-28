"""The AI provider layer: adapters, fallback, cooldown and recording.
Everything is faked: no network, no keys."""
import asyncio
import json
from types import SimpleNamespace

import httpx
import pytest

from app.ai.llm.providers import (
    AnthropicProvider,
    GeminiProvider,
    OpenAIProvider,
    merge_turns,
    split_system,
)
from app.ai.llm.router import COOLDOWN_SECONDS, FAILURES_BEFORE_COOLDOWN, LLMRouter, build_providers
from app.ai.llm.types import AIUnavailableError, LLMError, LLMRequest

MESSAGES = [
    {"role": "system", "content": "Be brief."},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello"},
    {"role": "user", "content": "Explain loops"},
]


def request(**over):
    return LLMRequest(messages=MESSAGES, purpose="mentor", **over)


def run(coro):
    return asyncio.run(coro)


# ---- message shaping ------------------------------------------------------------------------


def test_system_messages_are_split_off_and_joined():
    system, rest = split_system(
        [{"role": "system", "content": "a"}, {"role": "user", "content": "q"}, {"role": "system", "content": "b"}]
    )

    assert system == "a\n\nb"
    assert [m["role"] for m in rest] == ["user"]


def test_turns_alternate_and_start_with_the_user():
    turns = merge_turns(
        [
            {"role": "assistant", "content": "stray"},
            {"role": "user", "content": "one"},
            {"role": "user", "content": "two"},
            {"role": "assistant", "content": "ok"},
        ],
        assistant_role="assistant",
    )

    assert [t["role"] for t in turns] == ["user", "assistant"]
    assert turns[0]["content"] == "one\n\ntwo"


# ---- OpenAI -------------------------------------------------------------------------------------


class FakeOpenAI:
    def __init__(self, text="answer", boom=None):
        self.text, self.boom, self.kwargs = text, boom, None
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    async def create(self, **kwargs):
        self.kwargs = kwargs
        if self.boom:
            raise self.boom
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.text))],
            usage=SimpleNamespace(prompt_tokens=11, completion_tokens=7),
        )


def test_openai_adapter_passes_settings_and_reads_usage():
    fake = FakeOpenAI("hello")
    provider = OpenAIProvider("k", "gpt-x", 30, client=fake)

    result = run(provider.complete(request(temperature=0.2, max_tokens=500, json_mode=True)))

    assert (result.text, result.provider, result.model) == ("hello", "openai", "gpt-x")
    assert (result.input_tokens, result.output_tokens) == (11, 7)
    assert fake.kwargs["model"] == "gpt-x"
    assert fake.kwargs["max_completion_tokens"] == 500
    assert fake.kwargs["response_format"] == {"type": "json_object"}
    assert fake.kwargs["messages"] == MESSAGES


def test_openai_empty_answer_is_a_failure():
    provider = OpenAIProvider("k", "m", 30, client=FakeOpenAI("   "))

    with pytest.raises(LLMError, match="empty"):
        run(provider.complete(request()))


# ---- Gemini ----------------------------------------------------------------------------------------


def gemini_transport(captured, status=200, body=None):
    def handler(req: httpx.Request):
        captured["url"] = str(req.url)
        captured["json"] = json.loads(req.content)
        return httpx.Response(
            status,
            json=body
            if body is not None
            else {
                "candidates": [{"content": {"parts": [{"text": "from "}, {"text": "gemini"}]}}],
                "usageMetadata": {"promptTokenCount": 5, "candidatesTokenCount": 3},
            },
        )

    return httpx.MockTransport(handler)


def test_gemini_request_and_response():
    seen = {}
    provider = GeminiProvider("KEY", "gemini-x", 30, transport=gemini_transport(seen))

    result = run(provider.complete(request(json_mode=True, max_tokens=900)))

    assert result.text == "from gemini"
    assert (result.input_tokens, result.output_tokens) == (5, 3)
    assert "gemini-x:generateContent" in seen["url"] and "key=KEY" in seen["url"]
    body = seen["json"]
    assert body["systemInstruction"]["parts"][0]["text"] == "Be brief."
    assert [c["role"] for c in body["contents"]] == ["user", "model", "user"]
    assert body["generationConfig"]["responseMimeType"] == "application/json"
    assert body["generationConfig"]["maxOutputTokens"] == 900


def test_gemini_errors_and_empty_answers_fail():
    for transport in (
        gemini_transport({}, status=503),
        gemini_transport({}, body={"candidates": []}),
    ):
        provider = GeminiProvider("k", "m", 30, transport=transport)

        with pytest.raises(LLMError):
            run(provider.complete(request()))


# ---- Anthropic ----------------------------------------------------------------------------------------


def anthropic_transport(captured, status=200):
    def handler(req: httpx.Request):
        captured["headers"] = dict(req.headers)
        captured["json"] = json.loads(req.content)
        return httpx.Response(
            status,
            json={
                "content": [{"type": "text", "text": "from claude"}],
                "usage": {"input_tokens": 9, "output_tokens": 4},
            },
        )

    return httpx.MockTransport(handler)


def test_anthropic_request_and_response():
    seen = {}
    provider = AnthropicProvider("SECRET", "claude-x", 30, transport=anthropic_transport(seen))

    result = run(provider.complete(request(json_mode=True)))

    assert result.text == "from claude"
    assert (result.input_tokens, result.output_tokens) == (9, 4)
    assert seen["headers"]["x-api-key"] == "SECRET"
    assert seen["headers"]["anthropic-version"]
    body = seen["json"]
    assert body["model"] == "claude-x"
    assert body["system"].startswith("Be brief.") and "valid JSON" in body["system"]
    assert [m["role"] for m in body["messages"]] == ["user", "assistant", "user"]


def test_anthropic_http_error_fails():
    provider = AnthropicProvider("k", "m", 30, transport=anthropic_transport({}, status=429))

    with pytest.raises(LLMError, match="429"):
        run(provider.complete(request()))


# ---- the router ------------------------------------------------------------------------------------------


class Stub:
    def __init__(self, name, fail=False, text="ok"):
        self.name, self.model, self.fail, self.text, self.calls = name, f"{name}-model", fail, text, 0

    async def complete(self, req):
        self.calls += 1
        if self.fail:
            raise RuntimeError(f"{self.name} down: secret-detail")
        from app.ai.llm.types import LLMResult

        return LLMResult(text=self.text, provider=self.name, model=self.model, latency_ms=12,
                         input_tokens=3, output_tokens=2)


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def router(*providers, rows=None, clock=None):
    async def recorder(row):
        rows.append(row)

    return LLMRouter(list(providers), recorder=recorder if rows is not None else None,
                     clock=clock or Clock())


def test_the_first_working_provider_answers():
    a, b = Stub("a"), Stub("b")

    result = run(router(a, b).complete(request()))

    assert result.provider == "a" and result.fell_back_from == ()
    assert b.calls == 0


def test_a_failing_provider_falls_back_to_the_next():
    a, b = Stub("a", fail=True), Stub("b", text="from b")

    result = run(router(a, b).complete(request()))

    assert (result.provider, result.text) == ("b", "from b")
    assert result.fell_back_from == ("a",)


def test_when_every_provider_fails_the_caller_hears_about_it():
    with pytest.raises(AIUnavailableError, match="a, b"):
        run(router(Stub("a", fail=True), Stub("b", fail=True)).complete(request()))


def test_no_providers_configured():
    with pytest.raises(AIUnavailableError, match="No AI provider"):
        run(router().complete(request()))


def test_every_attempt_is_recorded_without_leaking_error_text():
    rows = []
    run(router(Stub("a", fail=True), Stub("b"), rows=rows).complete(
        LLMRequest(messages=MESSAGES, purpose="quiz", prompt_version="quiz-v1")
    ))

    assert [(r["provider"], r["success"]) for r in rows] == [("a", False), ("b", True)]
    assert rows[0]["error_type"] == "RuntimeError"
    assert "secret-detail" not in json.dumps(rows, default=str)
    assert rows[1]["input_tokens"] == 3 and rows[1]["latency_ms"] == 12
    assert all(r["purpose"] == "quiz" and r["prompt_version"] == "quiz-v1" for r in rows)


def test_a_broken_recorder_never_breaks_the_request():
    async def recorder(row):
        raise RuntimeError("database down")

    r = LLMRouter([Stub("a")], recorder=recorder)

    assert run(r.complete(request())).text == "ok"


def test_a_provider_that_keeps_failing_is_skipped_for_a_while():
    clock = Clock()
    a, b = Stub("a", fail=True), Stub("b")
    r = router(a, b, clock=clock)

    for _ in range(FAILURES_BEFORE_COOLDOWN):
        run(r.complete(request()))
    assert a.calls == FAILURES_BEFORE_COOLDOWN

    run(r.complete(request()))  # cooling down: not tried at all
    assert a.calls == FAILURES_BEFORE_COOLDOWN

    clock.now += COOLDOWN_SECONDS + 1
    run(r.complete(request()))  # cooldown over: tried again
    assert a.calls == FAILURES_BEFORE_COOLDOWN + 1


def test_a_success_clears_the_failure_count():
    a = Stub("a", fail=True)
    r = router(a, Stub("b"))

    run(r.complete(request()))
    run(r.complete(request()))
    a.fail = False
    run(r.complete(request()))
    a.fail = True
    run(r.complete(request()))
    run(r.complete(request()))

    assert a.calls == 5  # two failures, a success, two failures: never three in a row


def test_when_everything_is_cooling_down_it_tries_anyway():
    clock = Clock()
    a = Stub("a", fail=True)
    r = router(a, clock=clock)

    for _ in range(FAILURES_BEFORE_COOLDOWN):
        with pytest.raises(AIUnavailableError):
            run(r.complete(request()))

    a.fail = False

    assert run(r.complete(request())).provider == "a"


# ---- configuration -------------------------------------------------------------------------------------------


def fake_settings(**over):
    base = dict(
        OPENAI_API_KEY="o", GEMINI_API_KEY="g", ANTHROPIC_API_KEY="a",
        OPENAI_MODEL="om", GEMINI_MODEL="gm", ANTHROPIC_MODEL="am",
        AI_PROVIDERS="openai,gemini,anthropic", AI_REQUEST_TIMEOUT=10.0,
    )
    base.update(over)
    return SimpleNamespace(**base)


def test_providers_follow_the_configured_order():
    names = [p.name for p in build_providers(fake_settings(AI_PROVIDERS="anthropic, openai"))]

    assert names == ["anthropic", "openai"]


def test_providers_without_a_key_are_skipped():
    names = [p.name for p in build_providers(fake_settings(GEMINI_API_KEY="", ANTHROPIC_API_KEY=""))]

    assert names == ["openai"]


def test_unknown_and_repeated_names_are_ignored():
    names = [p.name for p in build_providers(fake_settings(AI_PROVIDERS="openai,mystery,openai"))]

    assert names == ["openai"]


def test_no_keys_means_no_providers():
    s = fake_settings(OPENAI_API_KEY="", GEMINI_API_KEY="", ANTHROPIC_API_KEY="")

    assert build_providers(s) == []


# ---- whose request it was ------------------------------------------------------------------------


def test_the_current_learner_is_recorded_without_being_passed_around(monkeypatch):
    from uuid import uuid4

    from app.ai import llm
    from app.ai.llm import use_profile

    rows = []

    async def recorder(row):
        rows.append(row)

    monkeypatch.setattr(llm, "get_router", lambda: LLMRouter([Stub("a")], recorder=recorder))

    mine, explicit = uuid4(), uuid4()

    async def scenario():
        use_profile(mine)
        await llm.complete_text(MESSAGES, purpose="quiz")
        await llm.complete_text(MESSAGES, purpose="quiz", profile_id=explicit)

    asyncio.run(scenario())

    assert [r["profile_id"] for r in rows] == [mine, explicit]  # an explicit id wins


def test_each_request_context_is_separate():
    from uuid import uuid4

    from app.ai.llm import use_profile
    from app.ai.llm.context import current_profile

    async def learner(pid, seen):
        use_profile(pid)
        await asyncio.sleep(0)
        seen.append(current_profile())

    async def scenario():
        a, b, seen = uuid4(), uuid4(), []
        await asyncio.gather(learner(a, seen), learner(b, seen))
        return a, b, seen, current_profile()

    a, b, seen, outer = asyncio.run(scenario())

    assert sorted(seen, key=str) == sorted([a, b], key=str)
    assert outer is None  # nothing leaked into the caller's context
