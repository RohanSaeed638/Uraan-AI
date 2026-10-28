from dataclasses import dataclass
from uuid import UUID


class LLMError(Exception):
    """One provider could not answer. The router moves on to the next."""

    def __init__(self, provider: str, message: str):
        super().__init__(f"{provider}: {message}")
        self.provider = provider


class AIUnavailableError(Exception):
    """No provider could answer (none configured, or every one failed)."""


@dataclass
class LLMRequest:
    """What every generator asks for, whichever provider answers.

    `messages` use the OpenAI shape: {"role": "system" | "user" | "assistant",
    "content": str}. `purpose` names the feature (roadmap, mentor, quiz...)
    and is recorded with every call, so usage and failures can be told apart.
    """

    messages: list[dict]
    purpose: str
    temperature: float = 0.4
    max_tokens: int = 1500
    json_mode: bool = False
    profile_id: UUID | None = None
    prompt_version: str | None = None


@dataclass
class LLMResult:
    text: str
    provider: str
    model: str
    latency_ms: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    # Providers that failed before this one answered, for example ["openai"].
    fell_back_from: tuple[str, ...] = ()
