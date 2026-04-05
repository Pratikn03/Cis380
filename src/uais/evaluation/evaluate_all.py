from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
REPORTS_DIR = REPO_ROOT / "reports"

METRIC_SOURCES = {
    "fraud": REPO_ROOT / "experiments" / "fraud" / "metrics" / "metrics.json",
    "cyber": REPO_ROOT / "experiments" / "cyber" / "metrics" / "metrics.json",
    "behavior": REPO_ROOT / "experiments" / "behavior" / "metrics" / "metrics.json",
    "recommender": REPO_ROOT / "experiments" / "recommender" / "metrics" / "metrics.json",
}


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except Exception:
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def _pick_metric(data: dict[str, Any] | None, key: str) -> float | None:
    if not data:
        return None
    val = data.get(key)
    return _safe_float(val)


def _extract_summary(name: str, data: dict[str, Any] | None) -> dict[str, Any] | None:
    if not data:
        return None

    if name in ("fraud", "cyber"):
        test = data.get("test", {})
        return {
            "name": name,
            "accuracy": _pick_metric(test, "accuracy"),
            "f1": _pick_metric(test, "f1"),
            "roc_auc": _pick_metric(test, "roc_auc"),
        }

    if name == "behavior":
        ae_acc = _pick_metric(data, "autoencoder_accuracy")
        lof_acc = _pick_metric(data, "lof_accuracy")
        acc = max([v for v in (ae_acc, lof_acc) if v is not None], default=None)
        return {
            "name": name,
            "accuracy": acc,
            "autoencoder_accuracy": ae_acc,
            "lof_accuracy": lof_acc,
        }

    if name == "recommender":
        return {
            "name": name,
            "accuracy": _pick_metric(data, "accuracy"),
        }

    return None


def main() -> None:
    summaries: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []

    for name, path in METRIC_SOURCES.items():
        payload = _load_json(path)
        summary = _extract_summary(name, payload)
        if summary is None:
            continue
        summaries.append(summary)
        if summary.get("accuracy") is not None:
            comparisons.append({"model": name, "accuracy": summary["accuracy"]})

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    summary_out = REPORTS_DIR / "evaluation_summary.json"
    comparison_out = REPORTS_DIR / "model_comparison.json"

    summary_payload = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "models": summaries,
    }
    with summary_out.open("w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2)

    with comparison_out.open("w", encoding="utf-8") as f:
        json.dump(comparisons, f, indent=2)

    print(f"Wrote {summary_out}")
    print(f"Wrote {comparison_out}")


if __name__ == "__main__":
    main()
