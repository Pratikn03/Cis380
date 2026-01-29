from __future__ import annotations

import os
from typing import Mapping, Sequence

from app.utils import LLMStub

try:
    from app.utils.gemini_client import GeminiClient
except ImportError:
    GeminiClient = None

if GeminiClient and os.getenv("GEMINI_API_KEY"):
    llm = GeminiClient()
else:
    llm = LLMStub()


def explain_decision(
    risks: Mapping[str, float], decision: str, context: Sequence[str] | None = None
) -> str:
    prompt_lines = [
        "You are a senior risk analyst AI. Explain the following decision based on the risk indicators.",
        "",
        "Risk Indicators (0-1 scale):",
    ]
    for key, value in risks.items():
        prompt_lines.append(f"- {key}: {value:.3f}")
    prompt_lines.append(f"\nSystem Decision: **{decision}**")
    if context:
        prompt_lines.append("\nContext:")
        prompt_lines.extend(context)

    prompt_lines.append(
        "\nProvide a clear, professional explanation for this decision suitable for a compliance log."
    )
    prompt = "\n".join(prompt_lines)
    return llm.generate(prompt)
