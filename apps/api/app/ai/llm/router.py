"""Tries the configured providers in order until one answers.

A provider that fails three times in a row is left alone for a minute, so a
provider outage costs one slow request, not one slow request per call. Every
attempt, good or bad, is recorded in `ai_requests`."""
import logging
import time

from app.ai.llm.providers import AnthropicProvider, GeminiProvider, OpenAIProvider
from app.ai.llm.types import AIUnavailableError, LLMRequest, LLMResult

logger = logging.getLogger(__name__)

FAILURES_BEFORE_COOLDOWN = 3
COOLDOWN_SECONDS = 60


class LLMRouter:
    def __init__(self, providers: list, recorder=None, clock=time.monotonic):
        self.providers = providers
        self.recorder = recorder
        self.clock = clock
        self._failures: dict[str, int] = {}
        self._cooling_until: dict[str, float] = {}

    def _usable(self) -> list:
        now = self.clock()
        ready = [p for p in self.providers if self._cooling_until.get(p.name, 0) <= now]

        # Everything cooling down: try them all rather than refuse outright.
        return ready or list(self.providers)

    def _failed(self, name: str) -> None:
        self._failures[name] = self._failures.get(name, 0) + 1

        if self._failures[name] >= FAILURES_BEFORE_COOLDOWN:
            self._cooling_until[name] = self.clock() + COOLDOWN_SECONDS
            self._failures[name] = 0

    def _worked(self, name: str) -> None:
        self._failures[name] = 0
        self._cooling_until.pop(name, None)

    async def _record(self, request: LLMRequest, provider, ok: bool, *, result=None, error=None, latency_ms=None):
        if self.recorder is None:
            return

        try:
            await self.recorder(
                {
                    "profile_id": request.profile_id,
                    "purpose": request.purpose,
                    "prompt_version": request.prompt_version,
                    "provider": provider.name,
                    "model": result.model if result else provider.model,
                    "success": ok,
                    "error_type": type(error).__name__ if error else None,
                    "latency_ms": result.latency_ms if result else latency_ms,
                    "input_tokens": result.input_tokens if result else None,
                    "output_tokens": result.output_tokens if result else None,
                }
            )
        except Exception:  # recording must never break a learner's request
            logger.exception("Could not record the AI request")

    async def complete(self, request: LLMRequest) -> LLMResult:
        if not self.providers:
            raise AIUnavailableError("No AI provider is configured.")

        failed: list[str] = []

        for provider in self._usable():
            started = self.clock()

            try:
                result = await provider.complete(request)
            except Exception as exc:
                logger.warning("AI provider %s failed for %s: %s", provider.name, request.purpose, exc)
                self._failed(provider.name)
                failed.append(provider.name)
                await self._record(
                    request, provider, False, error=exc,
                    latency_ms=int((self.clock() - started) * 1000),
                )
                continue

            self._worked(provider.name)
            result.fell_back_from = tuple(failed)
            await self._record(request, provider, True, result=result)

            return result

        raise AIUnavailableError(f"Every AI provider failed: {', '.join(failed)}")


def build_providers(settings) -> list:
    """The configured providers, in `AI_PROVIDERS` order, that have a key."""
    timeout = settings.AI_REQUEST_TIMEOUT
    makers = {
        "openai": lambda: OpenAIProvider(settings.OPENAI_API_KEY, settings.OPENAI_MODEL, timeout)
        if settings.OPENAI_API_KEY else None,
        "gemini": lambda: GeminiProvider(settings.GEMINI_API_KEY, settings.GEMINI_MODEL, timeout)
        if settings.GEMINI_API_KEY else None,
        "anthropic": lambda: AnthropicProvider(settings.ANTHROPIC_API_KEY, settings.ANTHROPIC_MODEL, timeout)
        if settings.ANTHROPIC_API_KEY else None,
    }
    providers = []

    for name in (n.strip().lower() for n in settings.AI_PROVIDERS.split(",")):
        maker = makers.get(name)
        provider = maker() if maker else None

        if provider is not None and all(p.name != provider.name for p in providers):
            providers.append(provider)

    return providers
