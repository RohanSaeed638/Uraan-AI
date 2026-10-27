"""One adapter per AI provider. Each turns an LLMRequest into that provider's
API call and the answer back into an LLMResult.

OpenAI uses its SDK; Gemini and Anthropic use their REST APIs over httpx, so
no extra dependencies are needed."""
import time

import httpx

from app.ai.llm.types import LLMError, LLMRequest, LLMResult

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

JSON_ONLY = "Respond with one valid JSON object and nothing else: no markdown fences, no commentary."


def _elapsed_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


def split_system(messages: list[dict]) -> tuple[str, list[dict]]:
    """(system text, the other messages). Several system messages are joined."""
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    rest = [m for m in messages if m["role"] != "system"]

    return system, rest


def merge_turns(messages: list[dict], assistant_role: str) -> list[dict]:
    """Chat APIs want strictly alternating turns that start with the user:
    merge neighbours with the same role and drop a leading assistant turn."""
    merged: list[dict] = []

    for message in messages:
        role = "user" if message["role"] == "user" else assistant_role

        if merged and merged[-1]["role"] == role:
            merged[-1]["content"] += "\n\n" + message["content"]
        else:
            merged.append({"role": role, "content": message["content"]})

    while merged and merged[0]["role"] != "user":
        merged.pop(0)

    return merged


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str, timeout: float, client=None):
        self.model = model
        self.timeout = timeout

        if client is None:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=api_key, timeout=timeout, max_retries=0)

        self.client = client

    async def complete(self, request: LLMRequest) -> LLMResult:
        started = time.monotonic()
        kwargs = {"response_format": {"type": "json_object"}} if request.json_mode else {}

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=request.messages,
            temperature=request.temperature,
            max_completion_tokens=request.max_tokens,
            **kwargs,
        )

        text = response.choices[0].message.content or ""

        if not text.strip():
            raise LLMError(self.name, "empty response")

        usage = getattr(response, "usage", None)

        return LLMResult(
            text=text,
            provider=self.name,
            model=self.model,
            latency_ms=_elapsed_ms(started),
            input_tokens=getattr(usage, "prompt_tokens", None),
            output_tokens=getattr(usage, "completion_tokens", None),
        )


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str, timeout: float, transport=None):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.transport = transport

    async def complete(self, request: LLMRequest) -> LLMResult:
        started = time.monotonic()
        system, rest = split_system(request.messages)
        turns = merge_turns(rest, assistant_role="model")

        body: dict = {
            "contents": [
                {"role": t["role"], "parts": [{"text": t["content"]}]} for t in turns
            ],
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            },
        }

        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}

        if request.json_mode:
            body["generationConfig"]["responseMimeType"] = "application/json"

        async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as http:
            response = await http.post(
                GEMINI_URL.format(model=self.model),
                params={"key": self.api_key},
                json=body,
            )

        if response.status_code >= 400:
            raise LLMError(self.name, f"HTTP {response.status_code}")

        data = response.json()
        candidates = data.get("candidates") or []
        parts = (candidates[0].get("content") or {}).get("parts") or [] if candidates else []
        text = "".join(p.get("text", "") for p in parts)

        if not text.strip():
            raise LLMError(self.name, "empty response")

        usage = data.get("usageMetadata") or {}

        return LLMResult(
            text=text,
            provider=self.name,
            model=self.model,
            latency_ms=_elapsed_ms(started),
            input_tokens=usage.get("promptTokenCount"),
            output_tokens=usage.get("candidatesTokenCount"),
        )


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str, model: str, timeout: float, transport=None):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.transport = transport

    async def complete(self, request: LLMRequest) -> LLMResult:
        started = time.monotonic()
        system, rest = split_system(request.messages)
        turns = merge_turns(rest, assistant_role="assistant")

        if request.json_mode:
            system = f"{system}\n\n{JSON_ONLY}".strip()

        body: dict = {
            "model": self.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": turns,
        }

        if system:
            body["system"] = system

        async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as http:
            response = await http.post(
                ANTHROPIC_URL,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": ANTHROPIC_VERSION,
                },
                json=body,
            )

        if response.status_code >= 400:
            raise LLMError(self.name, f"HTTP {response.status_code}")

        data = response.json()
        text = "".join(
            block.get("text", "")
            for block in data.get("content") or []
            if block.get("type") == "text"
        )

        if not text.strip():
            raise LLMError(self.name, "empty response")

        usage = data.get("usage") or {}

        return LLMResult(
            text=text,
            provider=self.name,
            model=self.model,
            latency_ms=_elapsed_ms(started),
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
        )
