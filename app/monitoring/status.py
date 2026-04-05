from __future__ import annotations

from typing import Final

READY: Final[str] = "ready"
DEGRADED: Final[str] = "degraded"
BLOCKED: Final[str] = "blocked"
ADVISORY: Final[str] = "advisory"

CANONICAL_STATUSES: Final[tuple[str, ...]] = (READY, DEGRADED, BLOCKED, ADVISORY)

_READY_ALIASES = {
    "ok",
    "ready",
    "green",
    "pass",
    "passed",
    "fresh",
}
_DEGRADED_ALIASES = {
    "warn",
    "warning",
    "yellow",
    "degraded",
    "needs_preprocess",
    "stale",
    "soft",
    "soft_gate",
}
_BLOCKED_ALIASES = {
    "missing",
    "error",
    "critical",
    "red",
    "fail",
    "failed",
    "mismatch",
    "blocked",
}
_ADVISORY_ALIASES = {"advisory", "historical", "manual"}


def _normalize_token(raw: str | None) -> str:
    return (raw or "").strip().lower().replace("-", "_")


def normalize_readiness_status(raw: str | None) -> str:
    token = _normalize_token(raw)
    if not token:
        return BLOCKED
    if token in _READY_ALIASES:
        return READY
    if token in _DEGRADED_ALIASES:
        return DEGRADED
    if token in _BLOCKED_ALIASES:
        return BLOCKED
    if token in _ADVISORY_ALIASES:
        return ADVISORY
    return token


def normalize_freshness_status(raw: str | None) -> str:
    token = _normalize_token(raw)
    if token in {"fresh", "stale", "missing"}:
        return token
    if token in {"ready", "ok", "green"}:
        return "fresh"
    if token in {"blocked", "missing", "red"}:
        return "missing"
    if token in {"warn", "warning", "yellow", "degraded"}:
        return "stale"
    return token or "missing"


def is_blocking_status(status: str | None) -> bool:
    return normalize_readiness_status(status) == BLOCKED

