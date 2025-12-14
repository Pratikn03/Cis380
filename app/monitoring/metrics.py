from __future__ import annotations

from pathlib import Path
from statistics import mean
from typing import Dict

from app.monitoring.logger import read_last_n_jsonl


def compute_metrics(log_path: Path, window_n: int = 1000) -> Dict[str, object]:
    entries = read_last_n_jsonl(log_path, window_n)
    if not entries:
        return {"count": 0, "avg_latency": 0.0, "avg_score": 0.0, "label_dist": {}}
    latencies = [entry.get("latency_ms", 0.0) for entry in entries]
    scores = [entry.get("prediction_score", 0.0) for entry in entries]
    label_dist: Dict[str, int] = {}
    for entry in entries:
        label = entry.get("prediction_label", "unknown")
        label_dist[label] = label_dist.get(label, 0) + 1
    return {
        "count": len(entries),
        "avg_latency": mean(latencies) if latencies else 0.0,
        "avg_score": mean(scores) if scores else 0.0,
        "label_dist": label_dist,
    }
