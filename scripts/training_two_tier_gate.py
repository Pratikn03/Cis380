#!/usr/bin/env python3
"""Generate core and extended training gates with explicit blocker reasons."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


@dataclass
class GateCheck:
    name: str
    status: str
    details: str


def _exists_check(name: str, rel_path: str) -> GateCheck:
    path = ROOT / rel_path
    ok = path.exists()
    return GateCheck(name=name, status="ok" if ok else "missing", details=rel_path)


def _dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _gate_status(checks: list[GateCheck], *, blocking: bool) -> tuple[str, list[str]]:
    blockers = [check.name for check in checks if check.status != "ok"]
    if not blockers:
        return ("green", blockers)
    return (("red" if blocking else "yellow"), blockers)


def main() -> int:
    preflight_core = _read_json(REPORTS / "training_preflight_core.json")
    preflight_extended = _read_json(REPORTS / "training_preflight_extended.json")

    core_checks = [
        _exists_check("fraud_metrics", "experiments/fraud/metrics/metrics.json"),
        _exists_check("cyber_metrics", "experiments/cyber/metrics/metrics.json"),
        _exists_check("behavior_metrics", "experiments/behavior/metrics/metrics.json"),
        _exists_check("fusion_metrics", "experiments/fusion/metrics/metrics.json"),
        _exists_check("recommender_metrics", "experiments/recommender/metrics/metrics.json"),
        _exists_check("voice_model", "models/voice_emotion.pkl"),
    ]
    if preflight_core.get("status") != "green":
        core_checks.append(
            GateCheck(
                name="preflight_core",
                status="missing",
                details="reports/training_preflight_core.json is not green",
            )
        )

    extended_checks = [
        _exists_check("video_temporal_metrics", "experiments/vision/video_temporal/metrics.json"),
        _exists_check("stt_eval_full", "reports/stt_eval_full.json"),
        _exists_check("brand_training_metrics", "experiments/vision/brand_logo/metrics.json"),
        _exists_check("face_emotion_model", "models/vision/face_emotion_model.pt"),
        _exists_check("vision_real_fake_model", "models/vision/deepfake_best.pt"),
    ]
    if preflight_extended.get("status") != "green":
        extended_checks.append(
            GateCheck(
                name="preflight_extended",
                status="warn",
                details="reports/training_preflight_extended.json is not green",
            )
        )

    core_status, core_blockers = _gate_status(core_checks, blocking=True)
    extended_status, extended_blockers = _gate_status(extended_checks, blocking=False)

    core_payload = {
        "generated_at": _now_utc(),
        "tier": "core",
        "status": core_status,
        "release_blocking": True,
        "checks": [asdict(check) for check in core_checks],
        "blockers": core_blockers,
    }
    extended_payload = {
        "generated_at": _now_utc(),
        "tier": "extended",
        "status": extended_status,
        "release_blocking": False,
        "checks": [asdict(check) for check in extended_checks],
        "blockers": extended_blockers,
    }

    _dump(REPORTS / "core_training_gate.json", core_payload)
    _dump(REPORTS / "extended_training_gate.json", extended_payload)
    print(json.dumps({"core": core_status, "extended": extended_status}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
