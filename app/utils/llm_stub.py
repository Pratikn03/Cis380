from __future__ import annotations

from typing import Sequence


class LLMStub:
    """Simple placeholder LLM client."""

    def generate(self, prompt: str, context: Sequence[str] | None = None) -> str:
        context_info = " | ".join(context) if context else "LLMStub"
        return f"{context_info} response to: {prompt.strip()}"
