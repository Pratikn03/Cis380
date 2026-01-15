from __future__ import annotations

import statistics
import time
from pathlib import Path
from typing import Any, Dict

import requests

BASE = "http://localhost:8000"
OUT = Path("reports/SYSTEM_SCORECARD.md")


def timed_post(path: str, payload: dict, n: int = 5) -> Dict[str, Any]:
    times = []
    last = None
    for _ in range(n):
        t0 = time.time()
        response = requests.post(BASE + path, json=payload, timeout=60)
        dt = (time.time() - t0) * 1000
        times.append(dt)
        last = response
    assert last is not None
    content_type = last.headers.get("content-type", "")
    if "application/json" in content_type:
        sample = last.json()
    else:
        sample = last.text
    return {
        "status": last.status_code,
        "p50_ms": round(statistics.median(times), 2),
        "p95_ms": round(sorted(times)[int(0.95 * (len(times) - 1))], 2),
        "sample_response": str(sample)[:400],
    }


def main() -> None:
    sections = ["# System Scorecard (Tier-6)", ""]

    post_checks = [
        ("Chat", "/api/chat", {"text": "hello", "mode": "auto"}),
        ("Fraud", "/api/fraud", {"amount": 123.45, "country": "US", "device": "ios", "velocity": 2}),
        ("Risk", "/api/risk/analyze", {"text": "suspicious login from new device"}),
        ("Voice Emotion", "/api/voice/emotion", {"text": "I am happy"}),
    ]

    sections.append("## Latency (p50/p95) + Status")
    for name, path, payload in post_checks:
        try:
            res = timed_post(path, payload, n=5)
            sections.append(f"### {name}")
            sections.append(f"- status: **{res['status']}**")
            sections.append(f"- p50: **{res['p50_ms']} ms**, p95: **{res['p95_ms']} ms**")
            sections.append(f"- sample: `{res['sample_response'].replace('`', '')}`")
            sections.append("")
        except Exception as exc:
            sections.append(f"### {name}")
            sections.append(f"- failed: {exc}")
            sections.append("")

    OUT.write_text("\n".join(sections), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
