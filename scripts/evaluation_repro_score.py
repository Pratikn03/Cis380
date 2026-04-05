#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
OUT_JSON = REPORTS / "EVALUATION_REPRO_SCORE.json"
OUT_MD = REPORTS / "EVALUATION_REPRO_SCORE.md"


@dataclass
class BucketScore:
    name: str
    points: float
    max_points: float
    note: str


def _load_json(path: Path) -> dict:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _artifact_gate_counts() -> tuple[int, int]:
    path = REPORTS / "ARTIFACT_GATE.md"
    if not path.exists():
        return 0, 0
    section = None
    req_ok = 0
    req_missing = 0
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.strip() == "## Required artifacts":
            section = "required"
            continue
        if line.strip() == "## Optional artifacts":
            section = "optional"
            continue
        if section != "required":
            continue
        if line.startswith("- ok:"):
            req_ok += 1
        elif line.startswith("- missing:"):
            req_missing += 1
    return req_ok, req_missing


def _claim_status_counts(claim_json: dict) -> tuple[int, int, int]:
    if not isinstance(claim_json, list):
        return 0, 0, 0
    proven = partial = missing = 0
    for row in claim_json:
        status = str(row.get("status", "")).lower()
        if status == "proven":
            proven += 1
        elif status == "partial":
            partial += 1
        else:
            missing += 1
    return proven, partial, missing


def _fresh_hours(path: Path) -> float | None:
    if not path.exists():
        return None
    return (datetime.now(timezone.utc) - datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)).total_seconds() / 3600.0


def _score_evaluation() -> tuple[list[BucketScore], float]:
    training_data = _load_json(REPORTS / "TRAINING_DATA.json")
    training_gaps = _load_json(REPORTS / "TRAINING_GAPS.json")
    project_audit = _load_json(REPORTS / "PROJECT_AUDIT.json")
    scorecard = _load_json(REPORTS / "SYSTEM_SCORECARD.json")
    claim_evidence = _load_json(REPORTS / "CLAIM_EVIDENCE.json")

    required = training_data.get("required") or []
    optional = training_data.get("optional") or []
    req_ok = sum(1 for row in required if row.get("status") == "ok")
    opt_ok = sum(1 for row in optional if row.get("status") == "ok")
    req_ratio = (req_ok / len(required)) if required else 0.0
    opt_ratio = (opt_ok / len(optional)) if optional else 0.0

    req_artifact_ok, req_artifact_missing = _artifact_gate_counts()
    missing_artifacts = len(training_gaps.get("missing_artifacts") or [])

    compile_errors = len(project_audit.get("py_compile_errors") or [])
    analyzed = int(project_audit.get("py_files_analyzed") or 0)

    checks = scorecard.get("checks") or []
    ok_checks = sum(1 for row in checks if row.get("ok"))
    check_ratio = (ok_checks / len(checks)) if checks else 0.0

    proven, partial, missing = _claim_status_counts(claim_evidence)
    claim_total = proven + partial + missing
    claim_ratio = ((proven + (0.5 * partial)) / claim_total) if claim_total else 0.0

    buckets = [
        BucketScore(
            name="Required Datasets",
            points=round(6.0 * req_ratio, 2),
            max_points=6.0,
            note=f"{req_ok}/{len(required)} required datasets healthy",
        ),
        BucketScore(
            name="Optional Datasets",
            points=round(2.0 * opt_ratio, 2),
            max_points=2.0,
            note=f"{opt_ok}/{len(optional)} optional datasets healthy",
        ),
        BucketScore(
            name="Artifact Readiness",
            points=5.0 if (missing_artifacts == 0 and req_artifact_missing == 0 and req_artifact_ok > 0) else 2.5,
            max_points=5.0,
            note=f"training_gaps_missing={missing_artifacts}, required_artifacts_missing={req_artifact_missing}",
        ),
        BucketScore(
            name="Static Quality Audit",
            points=4.0 if (compile_errors == 0 and analyzed > 0) else 1.5,
            max_points=4.0,
            note=f"py_compile_errors={compile_errors}, analyzed={analyzed}",
        ),
        BucketScore(
            name="Runtime Scorecard",
            points=round(5.0 * check_ratio, 2),
            max_points=5.0,
            note=f"{ok_checks}/{len(checks)} runtime checks healthy",
        ),
        BucketScore(
            name="Claims Verification",
            points=round(3.0 * claim_ratio, 2),
            max_points=3.0,
            note=f"proven={proven}, partial={partial}, missing={missing}",
        ),
    ]

    total = round(sum(bucket.points for bucket in buckets), 2)
    return buckets, total


def _score_reproducibility() -> tuple[list[BucketScore], float]:
    repro = _load_json(REPORTS / "REPRODUCIBILITY_CHECK.json")
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8", errors="ignore") if (ROOT / "Makefile").exists() else ""

    repro_score = float(repro.get("score") or 0.0)
    key_reports = [
        REPORTS / "TRAINING_DATA.json",
        REPORTS / "TRAINING_GAPS.json",
        REPORTS / "PROJECT_AUDIT.json",
        REPORTS / "SYSTEM_SCORECARD.json",
        REPORTS / "EVALUATION_REPRO_SCORE.json",
    ]
    fresh = 0
    for report in key_reports:
        age_h = _fresh_hours(report)
        if age_h is not None and age_h <= 168:
            fresh += 1
    fresh_ratio = fresh / len(key_reports)

    entrypoints = int("eval-evidence" in makefile) + int("repro-evidence" in makefile)
    entry_ratio = entrypoints / 2.0

    buckets = [
        BucketScore(
            name="Repro Check Score",
            points=round(8.0 * (repro_score / 100.0), 2),
            max_points=8.0,
            note=f"reproducibility_check_score={repro_score}",
        ),
        BucketScore(
            name="Automated Entrypoints",
            points=round(4.0 * entry_ratio, 2),
            max_points=4.0,
            note=f"entrypoints_found={entrypoints}/2",
        ),
        BucketScore(
            name="Report Freshness",
            points=round(3.0 * fresh_ratio, 2),
            max_points=3.0,
            note=f"fresh_reports={fresh}/{len(key_reports)} (<=7 days)",
        ),
    ]
    total = round(sum(bucket.points for bucket in buckets), 2)
    return buckets, total


def _render_md(
    *,
    generated_at: str,
    eval_buckets: list[BucketScore],
    eval_total: float,
    repro_buckets: list[BucketScore],
    repro_total: float,
) -> str:
    lines = [
        "# Evaluation + Reproducibility Score",
        "",
        f"- Generated: {generated_at}",
        "",
        "## Evaluation (out of 25)",
        "",
        "| Bucket | Points | Max | Notes |",
        "|---|---:|---:|---|",
    ]
    for bucket in eval_buckets:
        lines.append(f"| {bucket.name} | {bucket.points} | {bucket.max_points} | {bucket.note} |")
    lines.extend(["", f"**Evaluation Total: {eval_total}/25**", "", "## Reproducibility (out of 15)", "", "| Bucket | Points | Max | Notes |", "|---|---:|---:|---|"])
    for bucket in repro_buckets:
        lines.append(f"| {bucket.name} | {bucket.points} | {bucket.max_points} | {bucket.note} |")
    lines.extend(["", f"**Reproducibility Total: {repro_total}/15**"])
    return "\n".join(lines)


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    eval_buckets, eval_total = _score_evaluation()
    repro_buckets, repro_total = _score_reproducibility()

    payload = {
        "generated_at": generated_at,
        "evaluation": {
            "total": eval_total,
            "max": 25.0,
            "buckets": [bucket.__dict__ for bucket in eval_buckets],
        },
        "reproducibility": {
            "total": repro_total,
            "max": 15.0,
            "buckets": [bucket.__dict__ for bucket in repro_buckets],
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    OUT_MD.write_text(
        _render_md(
            generated_at=generated_at,
            eval_buckets=eval_buckets,
            eval_total=eval_total,
            repro_buckets=repro_buckets,
            repro_total=repro_total,
        ),
        encoding="utf-8",
    )
    print(f"wrote {OUT_MD}")
    print(f"wrote {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
