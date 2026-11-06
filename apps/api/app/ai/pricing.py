"""Rough cost of AI calls, for the admin's spend view and nothing else.

Prices are USD per one million tokens, as (input, output). They are the providers' published list
prices at the time of writing and WILL drift, so treat every figure as an estimate. A model that is
not listed is shown as "unpriced" (its tokens are still counted). Set `AI_PRICES` to a JSON object
such as {"my-model": [0.5, 2.0]} to add models or override these.
"""
import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

DEFAULT_PRICES: dict[str, tuple[float, float]] = {
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1": (2.00, 8.00),
    "gemini-2.5-flash": (0.30, 2.50),
}


def prices() -> dict[str, tuple[float, float]]:
    table = dict(DEFAULT_PRICES)

    if settings.AI_PRICES.strip():
        try:
            for model, pair in json.loads(settings.AI_PRICES).items():
                table[model] = (float(pair[0]), float(pair[1]))
        except Exception:
            logger.warning("AI_PRICES is not valid JSON of the form {model: [input, output]}; ignoring it")

    return table


def estimate_cost(model: str, input_tokens: int | None, output_tokens: int | None) -> float | None:
    """USD for one call, or None if the model has no known price."""
    price = prices().get(model)

    if price is None:
        return None

    return ((input_tokens or 0) * price[0] + (output_tokens or 0) * price[1]) / 1_000_000
