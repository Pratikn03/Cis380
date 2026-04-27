from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.promote_model import DEFAULT_GATES, evaluate_domain, load_gates

REPO_ROOT = Path(__file__).resolve().parents[3]
REPORTS_DIR = REPO_ROOT / "reports"


def _compact_thresholds(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "metric": item.get("metric"),
            "actual": item.get("actual"),
            "expected": item.get("expected"),
            "operator": item.get("operator"),
            "passed": item.get("passed"),
            "baseline": item.get("baseline"),
        }
        for item in result.get("thresholds", [])
    ]


def _summary_row(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": result["domain"],
        "status": "green" if result["status"] == "pass" else "red",
        "artifact": result.get("artifact"),
        "metricsFile": result.get("metricsFile"),
        "metrics": result.get("selectedMetrics", {}),
        "thresholds": _compact_thresholds(result),
        "failures": result.get("failures", []),
    }


def main() -> None:
    gates = load_gates(DEFAULT_GATES)
    required = list(gates.get("required_domains") or gates["domains"].keys())
    results = [
        evaluate_domain(domain, gates["domains"][domain], gates)
        for domain in required
        if domain in gates["domains"]
    ]
    summaries = [_summary_row(result) for result in results]
    comparisons = []
    for result in summaries:
        for metric, value in result.get("metrics", {}).items():
            if isinstance(value, (int, float)):
                comparisons.append(
                    {"model": result["name"], "metric": metric, "value": float(value)}
                )

    status = "green" if all(result["status"] == "green" for result in summaries) else "red"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "models": summaries,
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "evaluation_summary.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    (REPORTS_DIR / "model_comparison.json").write_text(
        json.dumps(comparisons, indent=2), encoding="utf-8"
    )
    print(f"Wrote {REPORTS_DIR / 'evaluation_summary.json'}")
    print(f"Wrote {REPORTS_DIR / 'model_comparison.json'}")
    if status != "green":
        raise SystemExit("Evaluation failed: one or more production domains are red.")


if __name__ == "__main__":
    main()
