from __future__ import annotations

import json
from pathlib import Path
from statistics import mean, pstdev
from typing import Dict, List

from app.monitoring.logger import safe_write_json

BASELINE_PATH = Path("data/monitoring/baseline/baseline_stats.json")


def build_baseline_stats(events: List[Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    stats: Dict[str, Dict[str, float]] = {}
    for feature in events[0].keys() if events else []:
        values = [event.get(feature, 0.0) for event in events]
        if not values:
            continue
        stats[feature] = {
            "mean": mean(values),
            "std": pstdev(values) if len(values) > 1 else 0.0,
            "min": min(values),
            "max": max(values),
        }
    return stats


def save_baseline(stats: Dict[str, Dict[str, float]], path: Path | None = None) -> None:
    target = path or BASELINE_PATH
    safe_write_json(target, {"features": stats})


def load_baseline(path: Path | None = None) -> Dict[str, Dict[str, float]]:
    target = path or BASELINE_PATH
    if not target.exists():
        return {}
    data = json.loads(target.read_text(encoding="utf-8"))
    return data.get("features", {})
