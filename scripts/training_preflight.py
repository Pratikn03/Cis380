#!/usr/bin/env python3
"""Two-tier dependency/data preflight for full retrain execution."""

from __future__ import annotations

import importlib.util
import json
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


@dataclass
class Check:
    name: str
    status: str
    details: str


def _pkg_check(name: str) -> Check:
    found = importlib.util.find_spec(name) is not None
    return Check(
        name=f"python:{name}",
        status="ok" if found else "missing",
        details="importable" if found else "module not importable",
    )


def _path_check(name: str, path: Path, *, allow_alt: bool = False) -> Check:
    exists = path.exists()
    if exists:
        return Check(name=name, status="ok", details=str(path))
    if allow_alt:
        return Check(name=name, status="warn", details=f"missing: {path}")
    return Check(name=name, status="missing", details=f"missing: {path}")


def _which_check(binary: str, *, severity: str = "required") -> Check:
    found = shutil.which(binary) is not None
    status = "ok" if found else ("warn" if severity == "optional" else "missing")
    return Check(
        name=f"system:{binary}",
        status=status,
        details="found" if found else "not found in PATH",
    )


def _write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _gate_status(checks: list[Check], *, fail_on: tuple[str, ...] = ("missing",)) -> str:
    return "green" if all(check.status not in fail_on for check in checks) else "red"


def main() -> int:
    core_checks = [
        _pkg_check("numpy"),
        _pkg_check("pandas"),
        _pkg_check("sklearn"),
        _pkg_check("joblib"),
        _pkg_check("soundfile"),
        _path_check("fraud_csv", ROOT / "data" / "raw" / "fraud" / "creditcard.csv"),
        _path_check("cyber_csv", ROOT / "data" / "raw" / "cyber" / "UNSW_NB15_training-set.csv"),
        _path_check("behavior_csv", ROOT / "data" / "raw" / "behavior" / "online_shoppers_intention.csv"),
        _path_check("voice_raw", ROOT / "data" / "raw" / "voice"),
    ]

    extended_checks = [
        _pkg_check("torch"),
        _pkg_check("transformers"),
        _pkg_check("datasets"),
        _pkg_check("ultralytics"),
        _which_check("ffmpeg", severity="optional"),
        _path_check("vision_real", ROOT / "data" / "raw" / "vision" / "train_real"),
        _path_check("vision_fake", ROOT / "data" / "raw" / "vision" / "train_fake"),
        _path_check("video_real", ROOT / "data" / "raw" / "vision" / "video" / "real"),
        _path_check("video_fake", ROOT / "data" / "raw" / "vision" / "video" / "fake"),
        _path_check("face_emotion", ROOT / "data" / "raw" / "vision" / "face_emotion", allow_alt=True),
        _path_check("brand_raw_primary", ROOT / "data" / "raw" / "brand" / "LogoDet-3K", allow_alt=True),
        _path_check("brand_raw_alt", ROOT / "data" / "raw" / "brand" / "logodet3k", allow_alt=True),
        _path_check("stt_audio_root", ROOT / "data" / "raw" / "voice" / "AudioWAV", allow_alt=True),
    ]

    core_payload = {
        "generated_at": _now_utc(),
        "tier": "core",
        "status": _gate_status(core_checks, fail_on=("missing",)),
        "checks": [asdict(check) for check in core_checks],
        "policy": "hard_gate",
    }
    extended_payload = {
        "generated_at": _now_utc(),
        "tier": "extended",
        "status": _gate_status(extended_checks, fail_on=("missing",)),
        "checks": [asdict(check) for check in extended_checks],
        "policy": "soft_gate",
        "note": "extended failures must be explicit but do not block core release gate",
    }

    _write(REPORTS / "training_preflight_core.json", core_payload)
    _write(REPORTS / "training_preflight_extended.json", extended_payload)
    print(json.dumps({"core": core_payload["status"], "extended": extended_payload["status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
