"""PlannerAgent — Claude tool-use loop.

Architecture: a single ``messages.create`` call runs in a loop. Each turn
the model emits ``tool_use`` blocks; we execute the matching ``Tool``
in-process, build ``tool_result`` blocks, append to the conversation, and
call ``messages.create`` again. The loop ends when the model returns
``stop_reason == "end_turn"`` or we hit ``AGENT_MAX_TOOL_CALLS``.

Prompt caching: the system prompt (tool catalogue + policies) is large and
static; we attach a ``cache_control`` breakpoint after it so subsequent
turns within the cache TTL pay the cheap cached-input rate. Extended
thinking is enabled for the planner; thinking tokens are streamed to the
caller as ``thinking_delta`` events when streaming is requested.

The loop yields a sequence of dict events that the orchestrator forwards
to the SSE endpoint:

  - {"type": "thinking_delta", "text": ...}      (extended thinking deltas)
  - {"type": "tool_call", "tool": ..., "args": ..., "tool_use_id": ...}
  - {"type": "tool_result", "tool": ..., "summary": ..., "data": ...}
  - {"type": "tool_error", "tool": ..., "error": ...}
  - {"type": "final_message", "text": ...}
  - {"type": "usage", "input_tokens": ..., "output_tokens": ..., ...}
  - {"type": "stop", "reason": ...}              (terminal event)
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Iterable, Iterator, Optional

from app.agent._anthropic import AnthropicUnavailable, get_anthropic_client
from app.agent.audit_logger import get_audit_logger
from app.agent.prompts import pick_variant
from app.agent.telemetry import record_tool
from app.agent.tools import ALL_TOOLS, ToolError, ToolExecutionContext, get_tool
from app.core import settings
from app.core.tracing import get_tracer

_tracer = get_tracer("sentifargo.agent")

_log = logging.getLogger("Sentifargo.agent.planner")


SYSTEM_PROMPT = """You are the planner for the Sentifargo intelligence platform.

Your job is to answer the user's request by calling internal tools. Each
tool wraps a real internal model or service; their results are
authoritative and must be used in your final answer.

Process:
1. Read the user's message and the triage signal.
2. Call the smallest set of tools needed to answer with high confidence.
3. If a tool errors, do not retry the same tool with identical args; pick a
   different tool, ask for missing data, or stop and explain.
4. When you have enough evidence, write the final answer in plain text.

Constraints:
- Do not fabricate tool results. If a tool says it failed, say so.
- Do not call tools to satisfy idle curiosity; minimise calls.
- Numerical scores from tools must be reported with two decimal places and
  the original units (0.78, not "78%" unless the tool returned a percent).
- Multi-domain questions are normal: e.g. for "is this image's brand
  counterfeit and is the user behaving suspiciously?" call ``brand_detect``
  and ``behavior_score`` and combine the evidence.
- Tool calls cost time and money. Do not exceed the configured budget.

Tool catalogue:
{tool_catalogue}
"""


@dataclass
class PlannerResult:
    """Final state after the loop terminates."""

    final_text: str
    evidence: list[dict[str, Any]]
    citations: list[dict[str, Any]]
    tool_calls: int
    stop_reason: str
    usage: dict[str, int]
    confidence: float
    error: Optional[str] = None


@dataclass
class _LoopState:
    messages: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    citations: list[dict[str, Any]] = field(default_factory=list)
    tool_calls: int = 0
    usage_total: dict[str, int] = field(default_factory=lambda: {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0,
    })


def _build_tool_catalogue() -> str:
    lines = []
    for tool in ALL_TOOLS:
        lines.append(f"- {tool.name}: {tool.description.splitlines()[0]}")
    return "\n".join(lines)


def _system_blocks(session_id: str | None = None) -> tuple[list[dict[str, Any]], str]:
    """System prompt as a single cached block. Returns (blocks, variant_id).

    The variant is chosen by ``app.agent.prompts.pick_variant`` so A/B
    splits are stable per session and the cache stays warm.
    """
    try:
        variant = pick_variant(session_id)
        body = variant.body
        variant_id = variant.id
    except Exception:  # pragma: no cover - prompt files missing
        body = SYSTEM_PROMPT
        variant_id = "fallback_inline"
    text = body.format(tool_catalogue=_build_tool_catalogue())
    return (
        [
            {
                "type": "text",
                "text": text,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        variant_id,
    )


def _tool_specs() -> list[dict[str, Any]]:
    return [tool.to_anthropic_schema() for tool in ALL_TOOLS]


def _accumulate_usage(state: _LoopState, response: Any) -> None:
    usage = getattr(response, "usage", None)
    if usage is None:
        return
    for key in state.usage_total:
        val = getattr(usage, key, 0) or 0
        state.usage_total[key] += int(val)


def _execute_tool(
    ctx: ToolExecutionContext, tool_name: str, raw_args: dict[str, Any]
) -> tuple[bool, str, dict[str, Any]]:
    """Run a tool. Returns ``(is_error, summary_text, data)``."""
    audit = get_audit_logger()
    started = time.perf_counter()
    span_cm = _tracer.start_as_current_span(f"agent.tool.{tool_name}")
    span = span_cm.__enter__()
    try:
        span.set_attribute("agent.trace_id", ctx.trace_id)
        span.set_attribute("agent.session_id", ctx.session_id)
    except Exception:
        pass
    try:
        tool = get_tool(tool_name)
        result = tool.run(ctx, raw_args)
    except ToolError as exc:
        latency_s = time.perf_counter() - started
        try:
            span.set_attribute("error", True)
            span.record_exception(exc)
        except Exception:
            pass
        span_cm.__exit__(None, None, None)
        audit.log_tool_span(
            ctx.trace_id,
            tool_name=tool_name,
            args_summary=json.dumps(raw_args, default=str)[:300],
            result_summary="",
            latency_ms=latency_s * 1000,
            error=str(exc),
        )
        record_tool(tool_name, latency_s, error=True)
        return True, str(exc), {}
    except Exception as exc:  # pragma: no cover - defensive
        latency_s = time.perf_counter() - started
        try:
            span.set_attribute("error", True)
            span.record_exception(exc)
        except Exception:
            pass
        span_cm.__exit__(None, None, None)
        audit.log_tool_span(
            ctx.trace_id,
            tool_name=tool_name,
            args_summary=json.dumps(raw_args, default=str)[:300],
            result_summary="",
            latency_ms=latency_s * 1000,
            error=f"unhandled: {exc}",
        )
        record_tool(tool_name, latency_s, error=True)
        return True, f"unhandled error: {exc}", {}

    latency_s = time.perf_counter() - started
    try:
        span.set_attribute("agent.tool.latency_ms", latency_s * 1000)
    except Exception:
        pass
    span_cm.__exit__(None, None, None)
    audit.log_tool_span(
        ctx.trace_id,
        tool_name=tool_name,
        args_summary=json.dumps(raw_args, default=str)[:300],
        result_summary=result.summary,
        latency_ms=latency_s * 1000,
    )
    record_tool(tool_name, latency_s, error=False)
    return False, result.summary, result.model_dump()


def _tool_result_block(tool_use_id: str, summary: str, data: dict[str, Any], is_error: bool) -> dict[str, Any]:
    """Build the tool_result content block to feed back to the model.

    The model sees the summary as the human-readable text and can read
    structured fields from the JSON we append. Keeping the JSON small
    matters: large RAG payloads should already be truncated by the tool.
    """
    payload_text = summary if is_error else json.dumps(data, default=str)[:6000]
    return {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": payload_text,
        "is_error": is_error,
    }


def _initial_user_message(user_message: str, triage_summary: dict[str, Any]) -> str:
    return (
        f"User message: {user_message}\n\n"
        f"Triage signal: {json.dumps(triage_summary, default=str)}\n\n"
        f"Plan the smallest set of tool calls that answers the request."
    )


def run_planner(
    *,
    user_message: str,
    triage_summary: dict[str, Any],
    ctx: ToolExecutionContext,
    extra_thinking: bool = False,
) -> Iterator[dict[str, Any]]:
    """Drive the tool-use loop. Yields events; final event is ``PlannerResult``
    wrapped in a ``{"type":"done","result":...}`` payload.
    """
    try:
        client = get_anthropic_client()
    except AnthropicUnavailable as exc:
        _log.info("planner LLM unavailable, falling back: %s", exc)
        yield {"type": "error", "message": str(exc)}
        yield {"type": "done", "result": _empty_result(str(exc))}
        return

    state = _LoopState()
    state.messages.append({"role": "user", "content": _initial_user_message(user_message, triage_summary)})

    thinking_budget = settings.agent.thinking_budget * (2 if extra_thinking else 1)
    system_blocks, prompt_variant = _system_blocks(session_id=ctx.session_id)
    yield {"type": "prompt_variant", "variant": prompt_variant}
    create_kwargs: dict[str, Any] = {
        "model": settings.agent.planner_model,
        "max_tokens": settings.agent.max_tokens_per_turn,
        "system": system_blocks,
        "tools": _tool_specs(),
    }
    if thinking_budget > 0:
        create_kwargs["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}

    final_text = ""
    stop_reason = "end_turn"
    confidence = 1.0

    while True:
        try:
            response = client.messages.create(messages=state.messages, **create_kwargs)
        except Exception as exc:
            _log.warning("planner messages.create failed: %s", exc)
            yield {"type": "error", "message": f"planner_call_failed: {exc}"}
            stop_reason = "error"
            break

        _accumulate_usage(state, response)

        # Surface thinking blocks (delta-style for SSE).
        for block in response.content or []:
            block_type = getattr(block, "type", None)
            if block_type == "thinking":
                thinking_text = getattr(block, "thinking", "") or ""
                if thinking_text:
                    yield {"type": "thinking_delta", "text": thinking_text}

        # Append the assistant turn verbatim (preserve thinking + tool_use).
        assistant_blocks = []
        for block in response.content or []:
            try:
                # Pydantic models dump cleanly; fall back to dict for raw blocks.
                if hasattr(block, "model_dump"):
                    assistant_blocks.append(block.model_dump())
                else:
                    assistant_blocks.append(dict(block))
            except Exception:  # pragma: no cover - defensive
                continue
        state.messages.append({"role": "assistant", "content": assistant_blocks})

        stop_reason = getattr(response, "stop_reason", "") or stop_reason

        if stop_reason != "tool_use":
            # Extract final text.
            for block in response.content or []:
                if getattr(block, "type", None) == "text":
                    final_text += block.text
            break

        # Run every tool_use block in this turn before going back to the model.
        tool_results: list[dict[str, Any]] = []
        for block in response.content or []:
            if getattr(block, "type", None) != "tool_use":
                continue
            if state.tool_calls >= settings.agent.max_tool_calls:
                _log.info("planner hit max_tool_calls=%s; stopping", settings.agent.max_tool_calls)
                yield {
                    "type": "tool_error",
                    "tool": block.name,
                    "error": "tool_call_budget_exhausted",
                }
                tool_results.append(
                    _tool_result_block(
                        block.id,
                        "tool_call_budget_exhausted",
                        {},
                        is_error=True,
                    )
                )
                stop_reason = "budget_exhausted"
                continue

            state.tool_calls += 1
            raw_args = block.input if isinstance(block.input, dict) else {}
            yield {
                "type": "tool_call",
                "tool": block.name,
                "args": raw_args,
                "tool_use_id": block.id,
            }
            is_error, summary, data = _execute_tool(ctx, block.name, raw_args)
            if is_error:
                yield {"type": "tool_error", "tool": block.name, "error": summary}
            else:
                yield {
                    "type": "tool_result",
                    "tool": block.name,
                    "summary": summary,
                    "data": data,
                }
                state.evidence.append(
                    {
                        "tool": block.name,
                        "summary": summary,
                        **{k: v for k, v in data.items() if k != "data"},
                    }
                )
                if data.get("citations"):
                    state.citations.extend(list(data["citations"]))

            tool_results.append(_tool_result_block(block.id, summary, data, is_error))

        if not tool_results:
            break

        state.messages.append({"role": "user", "content": tool_results})

        if stop_reason == "budget_exhausted":
            break

    # Heuristic confidence: high if we have evidence and stop_reason was natural.
    if state.evidence and stop_reason == "end_turn":
        confidence = 0.9
    elif stop_reason in {"end_turn"}:
        confidence = 0.7
    elif stop_reason == "budget_exhausted":
        confidence = 0.4
    else:
        confidence = 0.5

    yield {
        "type": "final_message",
        "text": final_text,
        "confidence": confidence,
    }
    yield {
        "type": "usage",
        **state.usage_total,
        "tool_calls": state.tool_calls,
    }
    yield {
        "type": "done",
        "result": PlannerResult(
            final_text=final_text,
            evidence=state.evidence,
            citations=state.citations,
            tool_calls=state.tool_calls,
            stop_reason=stop_reason,
            usage=state.usage_total,
            confidence=confidence,
        ),
    }


def _empty_result(error: str) -> PlannerResult:
    return PlannerResult(
        final_text="",
        evidence=[],
        citations=[],
        tool_calls=0,
        stop_reason="error",
        usage={"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0},
        confidence=0.0,
        error=error,
    )


__all__ = ["PlannerResult", "run_planner", "SYSTEM_PROMPT"]
