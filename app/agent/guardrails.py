"""Input + output guardrails for the multi-agent stack.

Two functions matter:

  * ``scrub_pii(text)`` — regex-based redaction for emails, SSNs,
    credit-card numbers, phone numbers, and IPs. Run before persisting a
    user message or shipping it to the LLM. Cheap, deterministic, and
    intentionally conservative — false positives are preferable to leaks.

  * ``classify_output(text)`` — uses a Haiku call to flag unsafe content
    in the synthesised final answer. Falls back to ``allow`` when the LLM
    is unavailable; we never block on the safety classifier alone since
    the planner has tool-call caps and the synthesis system prompt has
    its own instructions.

Both are invoked from the orchestrator at the appropriate boundary; tests
exercise them in isolation with crafted inputs.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Iterable

from app.agent._anthropic import AnthropicUnavailable, get_anthropic_client
from app.core import settings

_log = logging.getLogger("Sentifargo.agent.guardrails")


# ---------------------------------------------------------------------------
# PII scrubbing
# ---------------------------------------------------------------------------


_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
# Credit card detector. Use Luhn-friendly grouping; we don't validate the
# checksum because the goal is over-scrubbing, not under-scrubbing.
_CC_RE = re.compile(r"\b(?:\d[ -]?){13,19}\d\b")
# US-style and international phone numbers, loosely.
_PHONE_RE = re.compile(
    r"\b(?:\+?\d{1,3}[ -]?)?(?:\(?\d{3}\)?[ -]?)?\d{3}[ -]?\d{4}\b"
)
_IPV4_RE = re.compile(
    r"\b(?:25[0-5]|2[0-4]\d|[01]?\d\d?)(?:\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?)){3}\b"
)


@dataclass
class PIIRedactionResult:
    text: str
    counts: dict[str, int]

    @property
    def total(self) -> int:
        return sum(self.counts.values())


def scrub_pii(text: str) -> PIIRedactionResult:
    """Return ``text`` with PII tokens replaced by labelled placeholders.

    The placeholders survive into the LLM prompt so the model can still
    reason about structure (e.g. "the credit card was [REDACTED:CC]")
    without seeing the raw value.
    """
    counts = {"email": 0, "ssn": 0, "cc": 0, "phone": 0, "ip": 0}

    def _sub(pattern: re.Pattern, label: str, key: str) -> tuple[str, int]:
        nonlocal text
        replaced, n = pattern.subn(f"[REDACTED:{label}]", text)
        text = replaced
        return replaced, n

    counts["email"] = _sub(_EMAIL_RE, "EMAIL", "email")[1]
    counts["ssn"] = _sub(_SSN_RE, "SSN", "ssn")[1]
    counts["cc"] = _sub(_CC_RE, "CC", "cc")[1]
    counts["phone"] = _sub(_PHONE_RE, "PHONE", "phone")[1]
    counts["ip"] = _sub(_IPV4_RE, "IP", "ip")[1]
    return PIIRedactionResult(text=text, counts=counts)


# ---------------------------------------------------------------------------
# Output safety classifier
# ---------------------------------------------------------------------------


@dataclass
class SafetyVerdict:
    allow: bool
    reason: str = ""
    categories: tuple[str, ...] = ()


_SAFETY_SYSTEM = """You are a content safety classifier.

The text you receive is a chatbot response that will be returned to a
business user inside a risk + recommendation platform. Decide whether it
is safe to deliver as-is.

Output ONLY a JSON object:
  {"safe": <true|false>, "categories": [<list of: pii_leak, malicious_code, harmful_advice, prompt_injection, hate, sexual, violence>], "reason": <one short sentence>}

Default to safe. Only flag when there is a concrete violation."""


def classify_output(text: str) -> SafetyVerdict:
    """Run the cheap safety classifier on ``text``. Returns ``SafetyVerdict``."""
    if not text.strip():
        return SafetyVerdict(allow=True)
    if settings.agent.llm_mode == "offline":
        return SafetyVerdict(allow=True, reason="offline_mode")
    try:
        client = get_anthropic_client()
    except AnthropicUnavailable:
        return SafetyVerdict(allow=True, reason="classifier_unavailable")

    try:
        resp = client.messages.create(
            model=settings.agent.synthesis_model,
            max_tokens=256,
            system=_SAFETY_SYSTEM,
            messages=[{"role": "user", "content": text[:4000]}],
        )
    except Exception as exc:
        _log.warning("safety classifier call failed: %s", exc)
        return SafetyVerdict(allow=True, reason="classifier_error")

    blocks = [b for b in (resp.content or []) if getattr(b, "type", None) == "text"]
    if not blocks:
        return SafetyVerdict(allow=True, reason="empty_response")
    raw = blocks[0].text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:].lstrip()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        _log.warning("safety classifier returned non-JSON: %r", raw[:200])
        return SafetyVerdict(allow=True, reason="parse_failure")

    safe = bool(payload.get("safe", True))
    categories: Iterable[str] = payload.get("categories") or ()
    reason = str(payload.get("reason") or "")
    return SafetyVerdict(allow=safe, reason=reason, categories=tuple(categories))


REFUSAL_TEXT = (
    "I can't share that response. The output was flagged by the safety "
    "classifier. Please rephrase your request or contact an administrator."
)


__all__ = [
    "scrub_pii",
    "PIIRedactionResult",
    "classify_output",
    "SafetyVerdict",
    "REFUSAL_TEXT",
]
