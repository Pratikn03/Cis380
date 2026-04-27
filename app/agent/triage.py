"""TriageAgent — fast intent classification + entity extraction (Haiku).

Returns a structured ``TriageResult`` the planner uses to:
  * choose the initial subset of tools to expose,
  * pre-populate the blackboard with extracted entities,
  * decide whether to escalate (low confidence => deeper planner thinking).

Falls back to the existing keyword scorer (``app.agent.confidence``) when
``ANTHROPIC_API_KEY`` is missing or LLM_MODE=offline.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from pydantic import BaseModel, Field, ValidationError

from app.agent._anthropic import AnthropicUnavailable, get_anthropic_client
from app.agent.confidence import score_intent
from app.core import settings

_log = logging.getLogger("Sentifargo.agent.triage")


class TriageResult(BaseModel):
    intent: str = Field(..., description="Best-guess top-level intent.")
    confidence: float = Field(..., ge=0.0, le=1.0)
    entities: dict[str, Any] = Field(default_factory=dict)
    suggested_tools: list[str] = Field(default_factory=list)
    needs_escalation: bool = Field(default=False)
    source: str = Field(..., description="'llm' or 'keyword_fallback'.")


_SYSTEM_PROMPT = """You are the triage agent for a multi-modal risk and recommendation platform.

Output ONLY a JSON object that fits this schema:
  {
    "intent": "<one of: fraud, cyber, behavior, risk, voice_emotion, vision, brand, recommend, rag, chat>",
    "confidence": <float 0-1>,
    "entities": {<extracted entities like transaction_amount, login_country, brand_name, query, etc.>},
    "suggested_tools": [<list of tool names from: rag_search, fraud_score, cyber_score, behavior_score, risk_score, recommend, brand_detect, vision_analyze, voice_emotion, transcribe>]
  }

Rules:
- Pick exactly one primary intent. If genuinely multi-domain, pick the most prominent and let the planner fan out via tools.
- ``suggested_tools`` is a hint only; the planner is free to ignore it.
- For ambiguous greetings or small talk return intent="chat" with confidence=0.5.
- Do not include any text outside the JSON.
"""


def _llm_triage(text: str) -> Optional[TriageResult]:
    """Call Haiku for triage. Returns None if the SDK / key is missing or
    the LLM response can't be parsed."""
    if settings.agent.llm_mode == "offline":
        return None
    try:
        client = get_anthropic_client()
    except AnthropicUnavailable as exc:
        _log.debug("triage LLM unavailable: %s", exc)
        return None

    try:
        response = client.messages.create(
            model=settings.agent.triage_model,
            max_tokens=512,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": text}],
        )
    except Exception as exc:
        _log.warning("triage LLM call failed: %s", exc)
        return None

    text_blocks = [b for b in (response.content or []) if getattr(b, "type", None) == "text"]
    if not text_blocks:
        return None
    raw = text_blocks[0].text.strip()
    # Strip markdown fences if the model added them.
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:].lstrip()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        _log.warning("triage JSON parse failed: %s — raw=%r", exc, raw[:200])
        return None
    payload.setdefault("entities", {})
    payload.setdefault("suggested_tools", [])
    payload["needs_escalation"] = float(payload.get("confidence", 0)) < settings.agent.confidence_escalation_threshold
    payload["source"] = "llm"
    try:
        return TriageResult.model_validate(payload)
    except ValidationError as exc:
        _log.warning("triage schema mismatch: %s", exc.errors())
        return None


_INTENT_TO_TOOL: dict[str, list[str]] = {
    "fraud": ["fraud_score", "risk_score"],
    "cyber": ["cyber_score", "risk_score"],
    "behavior": ["behavior_score", "risk_score"],
    "risk": ["risk_score"],
    "voice_emotion": ["voice_emotion", "transcribe"],
    "vision": ["vision_analyze"],
    "brand": ["brand_detect"],
    "recommend": ["recommend"],
    "rag": ["rag_search"],
    "chat": [],
}


def _keyword_triage(text: str) -> TriageResult:
    """Fallback: reuse the existing keyword scorer."""
    intent_dict = score_intent(text)
    intent = intent_dict.get("intent", "chat")
    confidence = float(intent_dict.get("confidence", 0.5))
    return TriageResult(
        intent=intent,
        confidence=confidence,
        entities={},
        suggested_tools=_INTENT_TO_TOOL.get(intent, []),
        needs_escalation=confidence < settings.agent.confidence_escalation_threshold,
        source="keyword_fallback",
    )


def triage(text: str) -> TriageResult:
    """Classify intent and extract entities. LLM-first with keyword fallback."""
    result = _llm_triage(text)
    if result is None:
        return _keyword_triage(text)
    return result
