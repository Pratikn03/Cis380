from __future__ import annotations

import re

INJECTION_PATTERNS = [
    r"ignore (all|previous) instructions",
    r"system prompt",
    r"developer message",
    r"you are chatgpt",
    r"do anything now",
]

PII_PATTERNS = {
    "email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    "phone": r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
}


def looks_like_prompt_injection(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in INJECTION_PATTERNS)


def redact_pii(text: str) -> str:
    redacted = text
    for label, pattern in PII_PATTERNS.items():
        redacted = re.sub(pattern, f"[REDACTED_{label.upper()}]", redacted)
    return redacted
