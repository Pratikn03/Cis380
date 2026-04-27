"""Prometheus metrics for the multi-agent stack.

All metrics are wrapped in helpers that no-op gracefully when
``prometheus_client`` is missing or when ``PROMETHEUS_ENABLED=false`` so
tests and offline modes don't depend on the metric backend.
"""

from __future__ import annotations

import logging
import os
from typing import Any

_log = logging.getLogger("Sentifargo.agent.telemetry")

_ENABLED = os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true"

try:
    from prometheus_client import Counter, Gauge, Histogram  # type: ignore
except Exception:  # pragma: no cover - optional dep
    _ENABLED = False
    Counter = Gauge = Histogram = None  # type: ignore


def _noop(*_a: Any, **_kw: Any) -> None:
    return None


class _Stub:
    """Used when prometheus_client isn't installed. All methods no-op."""

    def labels(self, *_a: Any, **_kw: Any) -> "_Stub":
        return self

    def inc(self, *_a: Any, **_kw: Any) -> None:
        return None

    def observe(self, *_a: Any, **_kw: Any) -> None:
        return None

    def set(self, *_a: Any, **_kw: Any) -> None:
        return None


if _ENABLED and Counter is not None:
    AGENT_RUNS_TOTAL = Counter(
        "agent_runs_total",
        "Total agent runs.",
        labelnames=("intent", "stop_reason", "answer_source"),
    )
    AGENT_LATENCY_SECONDS = Histogram(
        "agent_latency_seconds",
        "End-to-end latency per agent run, including triage + planner + synthesis.",
        labelnames=("intent",),
        buckets=(0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0),
    )
    AGENT_TOOL_CALLS_TOTAL = Counter(
        "agent_tool_calls_total",
        "Tool invocations performed by the planner.",
        labelnames=("tool", "status"),  # status = ok | error
    )
    AGENT_TOOL_LATENCY_SECONDS = Histogram(
        "agent_tool_latency_seconds",
        "Per-tool execution latency.",
        labelnames=("tool",),
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0),
    )
    AGENT_TOKENS_TOTAL = Counter(
        "agent_tokens_total",
        "Cumulative tokens consumed by the planner.",
        labelnames=("kind",),  # input | output | cache_read | cache_creation
    )
    AGENT_CACHE_HIT_RATIO = Gauge(
        "agent_cache_hit_ratio",
        "Rolling cache_read / (cache_read + input) ratio across all runs.",
    )
    AGENT_CONFIDENCE = Histogram(
        "agent_confidence",
        "Final confidence per run.",
        labelnames=("intent",),
        buckets=(0.1, 0.3, 0.5, 0.7, 0.85, 0.95, 1.0),
    )
else:  # pragma: no cover - exercised only when prometheus is missing
    AGENT_RUNS_TOTAL = _Stub()
    AGENT_LATENCY_SECONDS = _Stub()
    AGENT_TOOL_CALLS_TOTAL = _Stub()
    AGENT_TOOL_LATENCY_SECONDS = _Stub()
    AGENT_TOKENS_TOTAL = _Stub()
    AGENT_CACHE_HIT_RATIO = _Stub()
    AGENT_CONFIDENCE = _Stub()


# Rolling totals for cache hit ratio (Prometheus Counters can't be divided
# inline; we keep small in-process accumulators and republish to a Gauge).
_cache_read_total = 0
_cache_input_total = 0  # input + cache_read tokens (the denominator)


def record_run(
    intent: str,
    stop_reason: str,
    answer_source: str,
    latency_seconds: float,
    confidence: float | None,
    tool_calls: int,
    usage: dict | None,
) -> None:
    """Emit Prometheus metrics for a completed agent run."""
    global _cache_read_total, _cache_input_total

    intent_label = (intent or "unknown")[:32]
    AGENT_RUNS_TOTAL.labels(intent=intent_label, stop_reason=stop_reason or "unknown", answer_source=answer_source or "unknown").inc()
    AGENT_LATENCY_SECONDS.labels(intent=intent_label).observe(latency_seconds)
    if confidence is not None:
        AGENT_CONFIDENCE.labels(intent=intent_label).observe(confidence)

    if usage:
        for kind in ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"):
            tokens = int(usage.get(kind) or 0)
            if tokens:
                AGENT_TOKENS_TOTAL.labels(kind=kind).inc(tokens)

        cache_read = int(usage.get("cache_read_input_tokens") or 0)
        input_tokens = int(usage.get("input_tokens") or 0)
        _cache_read_total += cache_read
        _cache_input_total += cache_read + input_tokens
        if _cache_input_total > 0:
            AGENT_CACHE_HIT_RATIO.set(_cache_read_total / _cache_input_total)


def record_tool(tool: str, latency_seconds: float, error: bool) -> None:
    AGENT_TOOL_CALLS_TOTAL.labels(tool=tool, status="error" if error else "ok").inc()
    AGENT_TOOL_LATENCY_SECONDS.labels(tool=tool).observe(latency_seconds)


__all__ = [
    "AGENT_RUNS_TOTAL",
    "AGENT_LATENCY_SECONDS",
    "AGENT_TOOL_CALLS_TOTAL",
    "AGENT_TOOL_LATENCY_SECONDS",
    "AGENT_TOKENS_TOTAL",
    "AGENT_CACHE_HIT_RATIO",
    "AGENT_CONFIDENCE",
    "record_run",
    "record_tool",
]
