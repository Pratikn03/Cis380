from __future__ import annotations

import io
import os
import statistics
import time
import wave
from pathlib import Path
from typing import Any, Dict

import requests

BASE = os.getenv("BASE_URL", "http://localhost:8000")
OUT = Path("reports/SYSTEM_SCORECARD.md")


def _sample_payload(response: requests.Response) -> str:
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        sample = response.json()
    else:
        sample = response.text
    return str(sample)[:400]


def timed_request(
    method: str,
    path: str,
    *,
    json_payload: dict | None = None,
    files: dict | None = None,
    n: int = 5,
) -> Dict[str, Any]:
    times: list[float] = []
    last: requests.Response | None = None
    for _ in range(n):
        t0 = time.time()
        if method == "GET":
            response = requests.get(BASE + path, timeout=60)
        elif method == "POST":
            response = requests.post(BASE + path, json=json_payload, files=files, timeout=60)
        else:
            raise ValueError(f"Unsupported method: {method}")
        times.append((time.time() - t0) * 1000)
        last = response
    assert last is not None
    return {
        "status": last.status_code,
        "p50_ms": round(statistics.median(times), 2),
        "p95_ms": round(sorted(times)[int(0.95 * (len(times) - 1))], 2),
        "sample_response": _sample_payload(last),
    }


def _silent_wav_bytes(duration_s: float = 0.5, sample_rate: int = 16000) -> bytes:
    frames = int(duration_s * sample_rate)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(b"\x00\x00" * frames)
    return buf.getvalue()


def _seed_dsa_docs(sections: list[str]) -> None:
    payload = {
        "filename": "scorecard_seed.txt",
        "content": "Sentifargo DSA answers questions using indexed documents with citations.",
    }
    try:
        response = requests.post(BASE + "/api/rag/ingest", json=payload, timeout=30)
        sections.append("## DSA Seed")
        sections.append(f"- status: **{response.status_code}**")
        sections.append(f"- sample: `{_sample_payload(response).replace('`', '')}`")
        sections.append("")
    except Exception as exc:
        sections.append("## DSA Seed")
        sections.append(f"- failed: {exc}")
        sections.append("")


def main() -> None:
    strict = os.getenv("SCORECARD_STRICT", "false").lower() in {"1", "true", "yes"}
    sections = ["# System Scorecard (Tier-6)", ""]
    failures: list[str] = []

    _seed_dsa_docs(sections)

    checks = [
        ("Health", "GET", "/api/health", None, None),
        ("Chat", "POST", "/api/chat", {"text": "hello", "use_rag": False}, None),
        ("Fraud", "POST", "/api/fraud", {"features": [0.0] * 30}, None),
        (
            "Risk",
            "POST",
            "/api/risk/analyze",
            {
                "login_country": "US",
                "device_known": True,
                "login_time": 12.0,
                "clicks_per_minute": 5.0,
                "files_accessed": 0,
                "transaction_amount": 20.0,
            },
            None,
        ),
        (
            "Voice Emotion",
            "POST",
            "/api/voice/emotion",
            None,
            {"file": ("sample.wav", _silent_wav_bytes(), "audio/wav")},
        ),
        ("DSA Docs", "POST", "/api/rag/ask", {"query": "How does Sentifargo DSA answer questions?"}, None),
    ]

    sections.append("## Latency (p50/p95) + Status")
    for name, method, path, json_payload, files in checks:
        try:
            res = timed_request(method, path, json_payload=json_payload, files=files, n=5)
            sections.append(f"### {name}")
            sections.append(f"- status: **{res['status']}**")
            sections.append(f"- p50: **{res['p50_ms']} ms**, p95: **{res['p95_ms']} ms**")
            sections.append(f"- sample: `{res['sample_response'].replace('`', '')}`")
            sections.append("")
        except Exception as exc:
            failures.append(f"{name}: {exc}")
            sections.append(f"### {name}")
            sections.append(f"- failed: {exc}")
            sections.append("")

    OUT.write_text("\n".join(sections), encoding="utf-8")
    print("wrote", OUT)

    if strict and failures:
        raise SystemExit(f"Scorecard failed: {', '.join(failures)}")


if __name__ == "__main__":
    main()
