"""Planner tool-use loop tests.

We mock ``anthropic.Anthropic`` so the loop runs deterministically and verify:
  (a) one round of tool_use → tool_result → end_turn flows correctly,
  (b) the planner respects the AGENT_MAX_TOOL_CALLS budget,
  (c) cache_read_input_tokens accumulates across responses,
  (d) tool errors surface as is_error tool_results without crashing,
  (e) confidence-driven escalation doubles the thinking budget.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Iterator
from unittest.mock import patch

import pytest

from app.agent import _anthropic, planner
from app.agent.tools._base import SessionAttachments, ToolExecutionContext


# ---------------------------------------------------------------------------
# fakes
# ---------------------------------------------------------------------------


class _FakeBlock(SimpleNamespace):
    def model_dump(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


class _FakeUsage(SimpleNamespace):
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0


class _FakeResponse(SimpleNamespace):
    pass


class _FakeMessages:
    """Programmable Anthropic Messages stub. Provide a list of pre-baked
    responses; each call to ``create`` returns the next one."""

    def __init__(self, responses: list[_FakeResponse]):
        self._responses = list(responses)
        self.create_calls: list[dict[str, Any]] = []

    def create(self, **kwargs):
        self.create_calls.append(kwargs)
        if not self._responses:
            raise RuntimeError("no more fake responses queued")
        return self._responses.pop(0)


class _FakeClient:
    def __init__(self, responses: list[_FakeResponse]):
        self.messages = _FakeMessages(responses)


def _text_response(text: str, usage: dict[str, int] | None = None) -> _FakeResponse:
    return _FakeResponse(
        content=[_FakeBlock(type="text", text=text)],
        stop_reason="end_turn",
        usage=_FakeUsage(**(usage or {})),
    )


def _tool_use_response(
    tool_name: str,
    tool_input: dict[str, Any],
    tool_use_id: str = "tu_1",
    usage: dict[str, int] | None = None,
) -> _FakeResponse:
    return _FakeResponse(
        content=[
            _FakeBlock(
                type="tool_use",
                id=tool_use_id,
                name=tool_name,
                input=tool_input,
            ),
        ],
        stop_reason="tool_use",
        usage=_FakeUsage(**(usage or {})),
    )


def _make_ctx() -> ToolExecutionContext:
    return ToolExecutionContext(
        session_id="s_test",
        user_id="u_test",
        trace_id="t_test",
        attachments=SessionAttachments(),
    )


def _drain(events: Iterator[dict[str, Any]]) -> tuple[list[dict[str, Any]], planner.PlannerResult | None]:
    collected: list[dict[str, Any]] = []
    result: planner.PlannerResult | None = None
    for event in events:
        collected.append(event)
        if event.get("type") == "done":
            result = event["result"]
    return collected, result


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _enable_llm(monkeypatch):
    """Force LLM mode on so the planner doesn't short-circuit, and clear the
    cached client so monkeypatched ones take effect."""
    from app.core import settings as settings_mod

    monkeypatch.setattr(settings_mod.agent, "llm_mode", "online", raising=False)
    _anthropic.reset_anthropic_client()
    yield
    _anthropic.reset_anthropic_client()


def test_round_trip_tool_use_then_text(monkeypatch):
    """Single tool round trip: tool_use → tool_result → final text."""
    fake = _FakeClient(
        [
            _tool_use_response(
                "fraud_score",
                {
                    "transaction_amount": 5000.0,
                    "device_known": False,
                    "login_country": "RU",
                },
                usage={"input_tokens": 100, "output_tokens": 20, "cache_creation_input_tokens": 80},
            ),
            _text_response(
                "Transaction fraud_risk=0.78 (high). Recommend manual review.",
                usage={"input_tokens": 50, "output_tokens": 30, "cache_read_input_tokens": 80},
            ),
        ]
    )
    monkeypatch.setattr(planner, "get_anthropic_client", lambda: fake)

    events, result = _drain(
        planner.run_planner(
            user_message="check this transaction",
            triage_summary={"intent": "fraud", "confidence": 0.9},
            ctx=_make_ctx(),
        )
    )

    types = [e["type"] for e in events]
    assert "tool_call" in types
    assert "tool_result" in types or "tool_error" in types
    assert "final_message" in types
    assert "done" in types
    assert result is not None
    assert result.tool_calls == 1
    assert result.stop_reason == "end_turn"
    assert result.final_text.startswith("Transaction")


def test_cache_read_tokens_accumulate(monkeypatch):
    """Each response's cache_read_input_tokens adds to the running total."""
    fake = _FakeClient(
        [
            _tool_use_response(
                "fraud_score",
                {"transaction_amount": 100.0, "device_known": True, "login_country": "US"},
                usage={"cache_creation_input_tokens": 200},
            ),
            _text_response(
                "Looks normal.",
                usage={"cache_read_input_tokens": 200, "input_tokens": 5, "output_tokens": 10},
            ),
        ]
    )
    monkeypatch.setattr(planner, "get_anthropic_client", lambda: fake)

    _events, result = _drain(
        planner.run_planner(
            user_message="quick check",
            triage_summary={"intent": "fraud", "confidence": 0.7},
            ctx=_make_ctx(),
        )
    )
    assert result is not None
    assert result.usage["cache_read_input_tokens"] == 200
    assert result.usage["cache_creation_input_tokens"] == 200


def test_max_tool_calls_budget(monkeypatch):
    """Loop must stop once max_tool_calls is hit even if the model keeps emitting tool_use blocks."""
    from app.core import settings as settings_mod

    monkeypatch.setattr(settings_mod.agent, "max_tool_calls", 2, raising=False)

    # Three tool_use turns followed by a hypothetical final text. The third
    # tool_use should be rejected as budget_exhausted; the loop ends after
    # that turn without consuming further responses.
    responses = [
        _tool_use_response(
            "fraud_score",
            {"transaction_amount": 1.0, "device_known": True, "login_country": "US"},
            tool_use_id="tu_1",
        ),
        _tool_use_response(
            "fraud_score",
            {"transaction_amount": 2.0, "device_known": True, "login_country": "US"},
            tool_use_id="tu_2",
        ),
        _tool_use_response(
            "fraud_score",
            {"transaction_amount": 3.0, "device_known": True, "login_country": "US"},
            tool_use_id="tu_3",
        ),
    ]
    fake = _FakeClient(responses)
    monkeypatch.setattr(planner, "get_anthropic_client", lambda: fake)

    _events, result = _drain(
        planner.run_planner(
            user_message="loop forever",
            triage_summary={"intent": "fraud", "confidence": 0.5},
            ctx=_make_ctx(),
        )
    )
    assert result is not None
    assert result.tool_calls == 2
    assert result.stop_reason == "budget_exhausted"


def test_invalid_tool_args_yield_error(monkeypatch):
    """If the model emits invalid args, the tool returns is_error=True and the loop continues."""
    fake = _FakeClient(
        [
            _tool_use_response(
                "fraud_score",
                {"transaction_amount": -100.0, "login_country": "US"},  # neg amount fails ge=0
                tool_use_id="tu_bad",
            ),
            _text_response("unable to score, request rejected"),
        ]
    )
    monkeypatch.setattr(planner, "get_anthropic_client", lambda: fake)

    events, result = _drain(
        planner.run_planner(
            user_message="bad transaction",
            triage_summary={"intent": "fraud", "confidence": 0.6},
            ctx=_make_ctx(),
        )
    )
    types = [e["type"] for e in events]
    assert "tool_error" in types
    assert result is not None
    assert result.stop_reason == "end_turn"


def test_extra_thinking_doubles_budget(monkeypatch):
    """When triage flags escalation, the planner doubles the thinking budget."""
    from app.core import settings as settings_mod

    monkeypatch.setattr(settings_mod.agent, "thinking_budget", 1000, raising=False)

    fake = _FakeClient([_text_response("done")])
    monkeypatch.setattr(planner, "get_anthropic_client", lambda: fake)

    _drain(
        planner.run_planner(
            user_message="ambiguous",
            triage_summary={"intent": "chat", "confidence": 0.4},
            ctx=_make_ctx(),
            extra_thinking=True,
        )
    )
    create_kwargs = fake.messages.create_calls[0]
    assert create_kwargs["thinking"]["budget_tokens"] == 2000


def test_unavailable_client_short_circuits(monkeypatch):
    """When the SDK isn't configured, run_planner emits an error+done immediately."""

    def _raise():
        raise _anthropic.AnthropicUnavailable("no key")

    monkeypatch.setattr(planner, "get_anthropic_client", _raise)
    events, result = _drain(
        planner.run_planner(
            user_message="hi",
            triage_summary={"intent": "chat", "confidence": 0.5},
            ctx=_make_ctx(),
        )
    )
    types = [e["type"] for e in events]
    assert "error" in types
    assert "done" in types
    assert result is not None
    assert result.stop_reason == "error"
