"""Multi-agent orchestrator.

Glue between the planner, triage and synthesis modules. Exposes two entry
points:

  * ``handle(text, ...)``: blocking; returns a final dict matching the
    legacy ``SentifargoOrchestrator.handle`` shape (``route``, ``answer``,
    ``meta``, ``intent_confidence``, ``latency_ms``, ``trace_id``).
  * ``stream(text, ...)``: generator that yields SSE-friendly events the
    HTTP layer forwards to the browser.

Falls back to the legacy keyword router when the Anthropic client is
unavailable or ``LLM_MODE=offline``.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Iterator, Mapping, Optional

from app.agent._anthropic import AnthropicUnavailable, get_anthropic_client
from app.agent.audit_logger import get_audit_logger
from app.agent.cost import estimate_cost
from app.agent.guardrails import REFUSAL_TEXT, classify_output, scrub_pii
from app.agent.memory import Blackboard, MemoryStore
from app.agent.planner import PlannerResult, run_planner
from app.agent.synthesis import SynthesisInput, synthesise
from app.agent.telemetry import record_run
from app.agent.tools._base import SessionAttachments, ToolExecutionContext
from app.agent.triage import TriageResult, triage
from app.core import settings

_log = logging.getLogger("Sentifargo.agent.multi_agent")


def _build_attachments(attachments: Mapping[str, Any] | None) -> SessionAttachments:
    if not attachments:
        return SessionAttachments()
    items: dict[str, bytes] = {}
    for key, value in attachments.items():
        if isinstance(value, (bytes, bytearray)):
            items[key] = bytes(value)
    return SessionAttachments(items=items)


def _llm_available() -> bool:
    if settings.agent.llm_mode == "offline":
        return False
    try:
        get_anthropic_client()
        return True
    except AnthropicUnavailable:
        return False


class MultiAgentOrchestrator:
    """Triage → Planner → Synthesis pipeline backed by Claude.

    Intentionally orthogonal to the legacy ``SentifargoOrchestrator`` so
    callers can pick either at runtime via ``LLM_MODE``.
    """

    def __init__(
        self,
        memory_store: Optional[MemoryStore] = None,
        blackboard: Optional[Blackboard] = None,
    ) -> None:
        self.memory = memory_store or MemoryStore.from_env()
        self.blackboard = blackboard or Blackboard.from_env()
        self.audit = get_audit_logger()

    # ------------------------------------------------------------------
    # public api
    # ------------------------------------------------------------------

    def handle(
        self,
        text: str,
        user_id: str = "anon",
        session_id: Optional[str] = None,
        attachments: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Blocking single-shot entrypoint. Drains the streaming generator
        and returns the final dict."""
        final: dict[str, Any] = {}
        for event in self.stream(
            text=text, user_id=user_id, session_id=session_id, attachments=attachments
        ):
            if event.get("type") == "final_envelope":
                final = event["envelope"]
        return final

    def stream(
        self,
        text: str,
        user_id: str = "anon",
        session_id: Optional[str] = None,
        attachments: Mapping[str, Any] | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Yield SSE-friendly events from the agent pipeline."""
        session_id = session_id or f"sess_{uuid.uuid4().hex[:10]}"
        started = time.perf_counter()

        # Scrub PII before persisting / sending to the LLM.
        scrubbed = scrub_pii(text)
        if scrubbed.total > 0:
            _log.info("scrubbed %d PII tokens from input", scrubbed.total)
            text = scrubbed.text

        trace_id = self.audit.log_trace_start(
            user_id=user_id,
            text=text,
            session_id=session_id,
            metadata={"source": "multi_agent", "pii_redacted": scrubbed.counts},
        )
        yield {
            "type": "trace_start",
            "trace_id": trace_id,
            "session_id": session_id,
            "pii_redacted": scrubbed.counts,
        }

        # ---- triage ----------------------------------------------------
        tri = triage(text)
        self.blackboard.set(session_id, "intent", tri.model_dump())
        yield {
            "type": "triage",
            "intent": tri.intent,
            "confidence": tri.confidence,
            "entities": tri.entities,
            "suggested_tools": tri.suggested_tools,
            "source": tri.source,
        }

        # ---- planner ---------------------------------------------------
        if not _llm_available():
            envelope = self._fallback_envelope(text, tri, trace_id, session_id, started)
            yield {"type": "final_envelope", "envelope": envelope}
            yield {"type": "trace_end", "trace_id": trace_id}
            return

        ctx = ToolExecutionContext(
            session_id=session_id,
            user_id=user_id,
            trace_id=trace_id,
            attachments=_build_attachments(attachments),
        )
        planner_result: Optional[PlannerResult] = None
        for event in run_planner(
            user_message=text,
            triage_summary=tri.model_dump(),
            ctx=ctx,
            extra_thinking=tri.needs_escalation,
        ):
            if event.get("type") == "done":
                planner_result = event["result"]
                continue
            yield event

        if planner_result is None:  # planner errored
            envelope = self._fallback_envelope(text, tri, trace_id, session_id, started, note="planner_unavailable")
            yield {"type": "final_envelope", "envelope": envelope}
            yield {"type": "trace_end", "trace_id": trace_id}
            return

        self.blackboard.set(session_id, "evidence", planner_result.evidence)
        self.blackboard.set(session_id, "citations", planner_result.citations)

        # ---- synthesis (only if planner did not produce a final text) --
        synth_payload = SynthesisInput(
            user_message=text,
            intent=tri.intent,
            evidence=planner_result.evidence,
            citations=planner_result.citations,
            confidence=planner_result.confidence,
        )
        if planner_result.final_text.strip():
            answer_text = planner_result.final_text
            answer_source = "planner"
        else:
            synth_out = synthesise(synth_payload)
            answer_text = synth_out.answer
            answer_source = synth_out.source

        # Output safety classifier (best-effort; never blocks on errors).
        verdict = classify_output(answer_text)
        if not verdict.allow:
            _log.warning(
                "safety classifier blocked answer: %s (categories=%s)",
                verdict.reason,
                verdict.categories,
            )
            yield {
                "type": "safety_blocked",
                "reason": verdict.reason,
                "categories": list(verdict.categories),
            }
            answer_text = REFUSAL_TEXT
            answer_source = "safety_refusal"

        self.memory.add_turn(user_id, text, answer_text)

        latency_ms = (time.perf_counter() - started) * 1000
        envelope = {
            "trace_id": trace_id,
            "session_id": session_id,
            "route": "agent",
            "answer": answer_text,
            "answer_source": answer_source,
            "intent": tri.intent,
            "intent_confidence": tri.confidence,
            "evidence": planner_result.evidence,
            "citations": planner_result.citations,
            "tool_calls": planner_result.tool_calls,
            "stop_reason": planner_result.stop_reason,
            "usage": planner_result.usage,
            "confidence": planner_result.confidence,
            "latency_ms": round(latency_ms, 2),
        }
        self.audit.log_trace_end(
            trace_id=trace_id,
            answer=answer_text,
            confidence=planner_result.confidence,
            latency_ms=latency_ms,
            usage=planner_result.usage,
            metadata={"intent": tri.intent, "tool_calls": planner_result.tool_calls},
        )
        record_run(
            intent=tri.intent,
            stop_reason=planner_result.stop_reason,
            answer_source=answer_source,
            latency_seconds=latency_ms / 1000.0,
            confidence=planner_result.confidence,
            tool_calls=planner_result.tool_calls,
            usage=planner_result.usage,
        )
        cost_usd = estimate_cost(settings.agent.planner_model, planner_result.usage)
        envelope["cost_usd"] = cost_usd

        # Active learning: push low-confidence runs onto the review queue.
        if (
            planner_result.confidence is not None
            and planner_result.confidence < settings.agent.confidence_escalation_threshold
        ):
            _enqueue_for_review(
                trace_id=trace_id,
                session_id=session_id,
                user_id=user_id,
                intent=tri.intent,
                user_message=text,
                answer=answer_text,
                confidence=planner_result.confidence,
                evidence=planner_result.evidence,
            )
            envelope["queued_for_review"] = True

        _persist_agent_call(
            trace_id=trace_id,
            session_id=session_id,
            user_id=user_id,
            intent=tri.intent,
            answer_source=answer_source,
            stop_reason=planner_result.stop_reason,
            tool_calls=planner_result.tool_calls,
            usage=planner_result.usage,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            confidence=planner_result.confidence,
            error=planner_result.error,
        )

        yield {"type": "final_envelope", "envelope": envelope}
        yield {"type": "trace_end", "trace_id": trace_id}

    # ------------------------------------------------------------------
    # offline fallback
    # ------------------------------------------------------------------

    def _fallback_envelope(
        self,
        text: str,
        tri: TriageResult,
        trace_id: str,
        session_id: str,
        started: float,
        note: str = "llm_offline",
    ) -> dict[str, Any]:
        """Use the legacy keyword orchestrator when Claude isn't available."""
        from app.agent.orchestrator import SentifargoOrchestrator

        legacy = SentifargoOrchestrator(memory_store=self.memory)
        legacy_result = legacy.handle(text=text, user_id="anon")
        latency_ms = (time.perf_counter() - started) * 1000
        envelope = {
            "trace_id": trace_id,
            "session_id": session_id,
            "route": legacy_result.get("route", tri.intent),
            "answer": legacy_result.get("answer", ""),
            "answer_source": "legacy_fallback",
            "intent": tri.intent,
            "intent_confidence": tri.confidence,
            "evidence": [],
            "citations": legacy_result.get("meta", {}).get("citations", []),
            "tool_calls": 0,
            "stop_reason": note,
            "usage": {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0},
            "confidence": tri.confidence,
            "latency_ms": round(latency_ms, 2),
        }
        self.audit.log_trace_end(
            trace_id=trace_id,
            answer=envelope["answer"],
            confidence=tri.confidence,
            latency_ms=latency_ms,
            usage=envelope["usage"],
            metadata={"intent": tri.intent, "fallback": note},
        )
        record_run(
            intent=tri.intent,
            stop_reason=note,
            answer_source="legacy_fallback",
            latency_seconds=latency_ms / 1000.0,
            confidence=tri.confidence,
            tool_calls=0,
            usage=envelope["usage"],
        )
        return envelope


def _enqueue_for_review(
    *,
    trace_id: str,
    session_id: str,
    user_id: str,
    intent: str,
    user_message: str,
    answer: str,
    confidence: float,
    evidence: list[dict],
) -> None:
    """Push a low-confidence run onto the review queue for analyst label.

    Best-effort; a failure here must never break the user response.
    """
    try:
        from app.db.models import ReviewQueue
        from app.db.session import SessionLocal
    except Exception as exc:
        _log.debug("review_queue persist skipped (db unavailable): %s", exc)
        return
    try:
        with SessionLocal() as session:
            row = ReviewQueue(
                trace_id=trace_id,
                session_id=session_id,
                user_id=user_id,
                intent=intent,
                payload={
                    "message": user_message,
                    "evidence": evidence[:20],
                },
                model_answer=answer[:4000] if answer else None,
                confidence=float(confidence) if confidence is not None else None,
                status="pending",
            )
            session.add(row)
            session.commit()
    except Exception as exc:
        _log.warning("review_queue persist failed: %s", exc)


def _persist_agent_call(
    *,
    trace_id: str,
    session_id: str,
    user_id: str,
    intent: str,
    answer_source: str,
    stop_reason: str,
    tool_calls: int,
    usage: dict,
    latency_ms: float,
    cost_usd: float,
    confidence: float | None,
    error: str | None,
) -> None:
    """Insert one row into agent_calls. Best-effort: a DB outage must not
    block the agent response."""
    try:
        from app.db.models import AgentCall
        from app.db.session import SessionLocal
    except Exception as exc:
        _log.debug("agent_calls persist skipped (db unavailable): %s", exc)
        return

    try:
        with SessionLocal() as session:
            row = AgentCall(
                trace_id=trace_id,
                session_id=session_id,
                user_id=user_id,
                intent=intent,
                answer_source=answer_source,
                stop_reason=stop_reason,
                tool_calls=tool_calls,
                input_tokens=int((usage or {}).get("input_tokens") or 0),
                output_tokens=int((usage or {}).get("output_tokens") or 0),
                cache_read_input_tokens=int((usage or {}).get("cache_read_input_tokens") or 0),
                cache_creation_input_tokens=int((usage or {}).get("cache_creation_input_tokens") or 0),
                latency_ms=float(latency_ms),
                cost_usd=float(cost_usd),
                confidence=float(confidence) if confidence is not None else None,
                error=error,
            )
            session.add(row)
            session.commit()
    except Exception as exc:
        _log.warning("agent_calls persist failed: %s", exc)


_default_orchestrator: Optional[MultiAgentOrchestrator] = None


def get_multi_agent() -> MultiAgentOrchestrator:
    """Lazy singleton for the default orchestrator."""
    global _default_orchestrator
    if _default_orchestrator is None:
        _default_orchestrator = MultiAgentOrchestrator()
    return _default_orchestrator


__all__ = ["MultiAgentOrchestrator", "get_multi_agent"]
