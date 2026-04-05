from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from app.rag.config import settings


def _read_jsonl(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def main() -> None:
    events = _read_jsonl(settings.logs_path)
    if not events:
        print("[rag-metrics] no events found")
        return

    by_day: dict[str, list[dict]] = defaultdict(list)
    for ev in events:
        ts = ev.get("ts")
        if not ts:
            continue
        day = time.strftime("%Y-%m-%d", time.gmtime(float(ts)))
        by_day[day].append(ev)

    summary = {}
    for day, items in by_day.items():
        latencies = [ev.get("latency_ms", 0.0) for ev in items]
        confidences = [
            ev.get("confidence", 0.0) for ev in items if ev.get("confidence") is not None
        ]
        failures = [ev.get("failure_reason") for ev in items if ev.get("failure_reason")]
        summary[day] = {
            "count": len(items),
            "avg_latency_ms": round(sum(latencies) / max(len(latencies), 1), 2),
            "avg_confidence": round(sum(confidences) / max(len(confidences), 1), 4),
            "failures": {reason: failures.count(reason) for reason in sorted(set(failures))},
        }

    metrics_path = Path("metrics") / "rag_daily.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("[rag-metrics] wrote", metrics_path)


if __name__ == "__main__":
    main()
