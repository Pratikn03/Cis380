"""Cost estimation for Anthropic Claude tokens.

Pricing changes; centralise here so every dashboard reads the same numbers
and we can update one constant when Anthropic publishes new rates.

Numbers below are per-million-token rates in USD as of late 2025; update by
editing ``MODEL_PRICES`` (the structure matches Anthropic's published
schedule). Cache reads are 0.1x input price; cache writes (creation) are
1.25x input price.
"""

from __future__ import annotations

# Rates per 1M tokens (USD).
MODEL_PRICES: dict[str, dict[str, float]] = {
    "claude-opus-4-7": {"input": 15.0, "output": 75.0},
    "claude-opus-4-6": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5": {"input": 0.80, "output": 4.0},
}

CACHE_READ_DISCOUNT = 0.10  # 10% of input rate
CACHE_WRITE_PREMIUM = 1.25  # 125% of input rate


def estimate_cost(model: str, usage: dict | None) -> float:
    """Return USD cost for a single ``messages.create`` response.

    ``usage`` keys: input_tokens, output_tokens, cache_read_input_tokens,
    cache_creation_input_tokens. Unknown models return 0 (we'd rather show
    no number than a wrong one).
    """
    if not usage:
        return 0.0
    rates = MODEL_PRICES.get(model)
    if rates is None:
        return 0.0
    input_rate = rates["input"] / 1_000_000.0
    output_rate = rates["output"] / 1_000_000.0
    cost = (
        int(usage.get("input_tokens") or 0) * input_rate
        + int(usage.get("output_tokens") or 0) * output_rate
        + int(usage.get("cache_read_input_tokens") or 0) * input_rate * CACHE_READ_DISCOUNT
        + int(usage.get("cache_creation_input_tokens") or 0) * input_rate * CACHE_WRITE_PREMIUM
    )
    return round(cost, 6)


__all__ = ["estimate_cost", "MODEL_PRICES"]
