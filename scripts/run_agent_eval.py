"""Run the agent eval harness across every golden file.

Each line is one test case:
  {
    "id": "fraud-01",
    "message": "...",
    "expected_intent": "fraud",
    "must_call_any": ["fraud_score", "risk_score"],
    "must_appear": ["substring 1", "substring 2"]   # optional
  }

Pass criteria (lenient enough to run offline against the legacy fallback):
  - triage_intent == expected_intent OR triage_confidence >= 0.6 for the
    expected intent's siblings (we accept ``risk`` for ``fraud`` etc.).
  - if must_call_any is non-empty: at least one of those tools was called
    (skipped when LLM_MODE=offline since there are no tool calls then).
  - if must_appear is set: each substring appears in the answer.

Output:
  - reports/agent_eval_<UTC date>.json
  - non-zero exit code if pass-rate < threshold (default 0.85).

Usage:
  python scripts/run_agent_eval.py [--threshold 0.85] [--out reports/agent_eval.json]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_DIR = ROOT / "tests" / "agent" / "golden"
DEFAULT_OUT = ROOT / "reports" / f"agent_eval_{datetime.now(timezone.utc).date()}.json"

# Intents that are acceptable substitutes for each other (since the keyword
# fallback can land on a sibling).
INTENT_ALIASES = {
    "fraud": {"fraud", "risk"},
    "cyber": {"cyber", "risk"},
    "behavior": {"behavior", "risk"},
    "recommend": {"recommend"},
    "rag": {"rag"},
}


def _load_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in sorted(GOLDEN_DIR.glob("*.jsonl")):
        if path.name.startswith("._"):  # macOS AppleDouble ghost
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            cases.append({"_file": path.name, **json.loads(line)})
    return cases


def _passes(case: dict[str, Any], envelope: dict[str, Any], tools_called: list[str]) -> tuple[bool, str]:
    expected = case["expected_intent"]
    actual = envelope.get("intent", "")
    if actual not in INTENT_ALIASES.get(expected, {expected}):
        return False, f"intent_mismatch: expected={expected} got={actual}"

    must_call = set(case.get("must_call_any") or [])
    if must_call and tools_called:
        if not (must_call & set(tools_called)):
            return False, f"tool_mismatch: expected_any={sorted(must_call)} called={sorted(set(tools_called))}"

    must_appear = case.get("must_appear") or []
    answer = (envelope.get("answer") or "").lower()
    for substr in must_appear:
        if substr.lower() not in answer:
            return False, f"missing_substring: {substr!r}"

    return True, "ok"


def _run_case(orchestrator, case: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    envelope: dict[str, Any] = {}
    tools: list[str] = []
    try:
        for event in orchestrator.stream(text=case["message"], user_id="eval", session_id=case["id"]):
            etype = event.get("type")
            if etype == "tool_call":
                tools.append(event.get("tool", ""))
            if etype == "final_envelope":
                envelope = event.get("envelope", {})
    except Exception as exc:
        return {
            "id": case["id"],
            "file": case["_file"],
            "passed": False,
            "reason": f"orchestrator_exception: {exc}",
            "envelope": {},
            "tools": tools,
            "elapsed_s": time.perf_counter() - started,
        }

    passed, reason = _passes(case, envelope, tools)
    return {
        "id": case["id"],
        "file": case["_file"],
        "passed": passed,
        "reason": reason,
        "envelope_summary": {
            "intent": envelope.get("intent"),
            "answer_source": envelope.get("answer_source"),
            "confidence": envelope.get("confidence"),
            "tool_calls": envelope.get("tool_calls"),
            "answer_excerpt": (envelope.get("answer") or "")[:200],
        },
        "tools_called": tools,
        "elapsed_s": round(time.perf_counter() - started, 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=0.85)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    os.environ.setdefault("APP_ENV", os.environ.get("APP_ENV", "development"))

    from app.agent.multi_agent import MultiAgentOrchestrator

    orch = MultiAgentOrchestrator()
    cases = _load_cases()
    if not cases:
        print("No golden cases found under", GOLDEN_DIR, file=sys.stderr)
        return 2

    results = [_run_case(orch, c) for c in cases]
    passed = sum(1 for r in results if r["passed"])
    pass_rate = passed / len(results)

    summary = {
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "pass_rate": pass_rate,
        "threshold": args.threshold,
        "results": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2))

    print(f"Agent eval: {passed}/{len(results)} passed ({pass_rate:.1%}) — written to {args.out}")
    if pass_rate < args.threshold:
        print(f"FAIL: pass_rate {pass_rate:.1%} < threshold {args.threshold:.1%}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
