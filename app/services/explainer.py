from __future__ import annotations

from typing import Mapping, Sequence

from app.utils import LLMStub

llm = LLMStub()


def explain_decision(risks: Mapping[str, float], decision: str, context: Sequence[str] | None = None) -> str:
    prompt_lines = ["Explain the risk decision:"]
    for key, value in risks.items():
        prompt_lines.append(f"- {key}: {value:.3f}")
    prompt_lines.append(f"Decision: {decision}")
    if context:
        prompt_lines.append("Context:")
        prompt_lines.extend(context)
    prompt = "\n".join(prompt_lines)
    return llm.generate(prompt)
