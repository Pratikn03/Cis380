"""Lazy Anthropic client construction shared by triage / planner / synthesis.

Importing ``anthropic`` is cheap, but instantiating ``Anthropic()`` requires
``ANTHROPIC_API_KEY`` to be set. We don't want module-level side effects, so
each agent calls ``get_anthropic_client()`` inside its hot path. The client
itself is a singleton per process (cached by ``functools.lru_cache``).

Tests can monkeypatch ``get_anthropic_client`` to inject a fake client.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any


class AnthropicUnavailable(RuntimeError):
    """Raised when an LLM call is attempted but the SDK / key is missing."""


@lru_cache(maxsize=1)
def get_anthropic_client() -> Any:
    """Return a cached Anthropic client. Raises AnthropicUnavailable if the
    SDK is missing or no API key is configured."""
    try:
        from anthropic import Anthropic  # type: ignore
    except Exception as exc:
        raise AnthropicUnavailable(f"anthropic SDK not installed: {exc}") from exc

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise AnthropicUnavailable(
            "ANTHROPIC_API_KEY is not set; set it in .env.local or your shell environment"
        )
    return Anthropic(api_key=api_key)


def reset_anthropic_client() -> None:
    """Clear the cached client. Used by tests after monkeypatching env vars."""
    get_anthropic_client.cache_clear()
