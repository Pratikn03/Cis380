"""SynthesisAgent — turns planner evidence into a final user-facing answer
with [n] citation markers (Haiku). Falls back to a deterministic template
when the LLM is unavailable so the agent stack still produces an answer.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import BaseModel, Field

from app.agent._anthropic import AnthropicUnavailable, get_anthropic_client
from app.core import settings

_log = logging.getLogger("Sentifargo.agent.synthesis")


class SynthesisInput(BaseModel):
    user_message: str
    intent: str
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = 1.0


class SynthesisOutput(BaseModel):
    answer: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float
    source: str  # "llm" or "template"


_SYNTH_SYSTEM = """You are the synthesis agent. The planner has gathered evidence from internal tools.

Write a concise, professional answer to the user. Rules:
- Cite evidence inline using [1], [2], ... where the numbers correspond to
  the order the evidence was provided. Only cite items the user can verify
  (RAG sources, scores, detections). Do not invent citations.
- Lead with the answer, not the methodology.
- If the planner's confidence is low, explicitly say so in one sentence and
  recommend the next action (escalate, gather more data, etc.).
- Do not mention internal tool names, models, or the agent architecture.
- Preserve numerical precision: if a tool returned 0.78, render "0.78" not "high".
- Length: 2-6 sentences for chat answers; bulleted lists OK for itemised
  results (recommendations, detections).
"""


def _llm_synthesise(payload: SynthesisInput) -> SynthesisOutput | None:
    if settings.agent.llm_mode == "offline":
        return None
    try:
        client = get_anthropic_client()
    except AnthropicUnavailable as exc:
        _log.debug("synthesis LLM unavailable: %s", exc)
        return None

    user_block = (
        f"User question:\n{payload.user_message}\n\n"
        f"Triaged intent: {payload.intent} (confidence={payload.confidence:.2f})\n\n"
        f"Evidence (numbered):\n{json.dumps(payload.evidence, indent=2, default=str)}\n"
    )
    try:
        response = client.messages.create(
            model=settings.agent.synthesis_model,
            max_tokens=1024,
            system=_SYNTH_SYSTEM,
            messages=[{"role": "user", "content": user_block}],
        )
    except Exception as exc:
        _log.warning("synthesis LLM call failed: %s", exc)
        return None

    text_blocks = [b for b in (response.content or []) if getattr(b, "type", None) == "text"]
    answer = text_blocks[0].text.strip() if text_blocks else ""
    if not answer:
        return None
    return SynthesisOutput(
        answer=answer,
        citations=payload.citations,
        confidence=payload.confidence,
        source="llm",
    )


def _template_synthesise(payload: SynthesisInput) -> SynthesisOutput:
    """Deterministic fallback: stitch evidence summaries into bullet lines."""
    if not payload.evidence:
        answer = (
            "I couldn't gather any tool evidence for this request. "
            "Please rephrase or attach a relevant file."
        )
        return SynthesisOutput(
            answer=answer, citations=[], confidence=payload.confidence, source="template"
        )

    lines = [f"**{payload.intent.upper()} analysis:**", ""]
    for idx, item in enumerate(payload.evidence, start=1):
        summary = item.get("summary") or item.get("tool") or "evidence"
        lines.append(f"[{idx}] {summary}")
    answer = "\n".join(lines)
    return SynthesisOutput(
        answer=answer,
        citations=payload.citations,
        confidence=payload.confidence,
        source="template",
    )


def synthesise(payload: SynthesisInput) -> SynthesisOutput:
    """Produce the user-facing answer. LLM-first with template fallback."""
    result = _llm_synthesise(payload)
    if result is not None:
        return result
    return _template_synthesise(payload)
