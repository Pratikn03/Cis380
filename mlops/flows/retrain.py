"""Auto-retrain trigger.

Reads the latest drift report and counts pending labeled rows in
``review_queue``. When either signal exceeds the configured trigger, runs
the appropriate ``dvc repro <stage>`` and ``scripts/promote_model.py
--domain <name>`` to roll a fresh artifact forward.

This is intentionally cron-friendly: idempotent, exits non-zero on any
trigger so an external scheduler (cron, systemd timer, or Prefect
deployment) can decide whether to alert on it.

Trigger logic:

  * Drift in domain D            → retrain D
  * Pending labels in domain D > N → retrain D

Domains map 1-1 to DVC stages. Recognised stages match the names from
``dvc.yaml`` and the ``promote_model.py`` ``--domain`` flag.

Run manually:

    python -m mlops.flows.retrain --label-trigger 50 --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

_log = logging.getLogger("Sentifargo.mlops.retrain")

DRIFT_REPORT_DIR = Path("reports/drift")

DOMAIN_TO_DVC_STAGE = {
    "fraud": "train_fraud_model",
    "cyber": "train_cyber_model",
    "behavior": "train_behavior_model",
    "recommender": "train_recommender",
    "vision": "train_vision_model",
    "brand": "train_brand_model",
}


def _latest_drift() -> dict | None:
    if not DRIFT_REPORT_DIR.exists():
        return None
    files = sorted(DRIFT_REPORT_DIR.glob("drift_*.json"))
    if not files:
        return None
    try:
        return json.loads(files[-1].read_text())
    except Exception:
        return None


def _drifted_domains(report: dict | None) -> set[str]:
    if not report:
        return set()
    return {f["domain"] for f in (report.get("findings") or []) if f.get("drifted")}


def _label_counts() -> dict[str, int]:
    """Count labeled rows in review_queue per intent. Empty when DB is unreachable."""
    try:
        from sqlalchemy import func

        from app.db.models import ReviewQueue
        from app.db.session import SessionLocal
    except Exception as exc:
        _log.info("review_queue read skipped (db unavailable): %s", exc)
        return {}
    try:
        with SessionLocal() as session:
            rows = (
                session.query(ReviewQueue.intent, func.count(ReviewQueue.id))
                .filter(ReviewQueue.status == "labeled")
                .group_by(ReviewQueue.intent)
                .all()
            )
            return {intent or "unknown": int(count) for intent, count in rows}
    except Exception as exc:
        _log.warning("review_queue read failed: %s", exc)
        return {}


def _decide_retrains(
    drifted: Iterable[str], label_counts: dict[str, int], label_trigger: int
) -> list[str]:
    domains: set[str] = set()
    domains.update(d for d in drifted if d in DOMAIN_TO_DVC_STAGE)
    for d, count in label_counts.items():
        if count >= label_trigger and d in DOMAIN_TO_DVC_STAGE:
            domains.add(d)
    return sorted(domains)


def _run(cmd: list[str], dry_run: bool) -> int:
    _log.info("$ %s", " ".join(cmd))
    if dry_run:
        return 0
    return subprocess.run(cmd, check=False).returncode


def retrain(domains: Iterable[str], dry_run: bool = False) -> dict[str, int]:
    results: dict[str, int] = {}
    for d in domains:
        stage = DOMAIN_TO_DVC_STAGE[d]
        rc = _run(["dvc", "repro", "--single-item", stage], dry_run=dry_run)
        if rc != 0:
            _log.warning("dvc repro %s failed (rc=%s); skipping promote", stage, rc)
            results[d] = rc
            continue
        rc = _run(["python", "scripts/promote_model.py", "--domain", d, "--promote-passing"], dry_run=dry_run)
        results[d] = rc
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label-trigger", type=int, default=int(os.getenv("RETRAIN_LABEL_TRIGGER", "50")))
    parser.add_argument("--dry-run", action="store_true", help="Log commands without executing.")
    parser.add_argument("--domain", action="append", help="Force retrain a specific domain (repeatable).")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if args.domain:
        domains = sorted({d for d in args.domain if d in DOMAIN_TO_DVC_STAGE})
        _log.info("forced domains: %s", domains)
    else:
        report = _latest_drift()
        drifted = _drifted_domains(report)
        labels = _label_counts()
        domains = _decide_retrains(drifted, labels, args.label_trigger)
        _log.info(
            "decision drifted=%s labels=%s trigger=%s → domains=%s",
            sorted(drifted),
            labels,
            args.label_trigger,
            domains,
        )

    if not domains:
        _log.info("no retrains required")
        return 0

    results = retrain(domains, dry_run=args.dry_run)
    out_dir = Path("reports/retrain")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"retrain_{datetime.now(timezone.utc).date()}.json"
    out.write_text(json.dumps({"results": results, "ran_at": datetime.now(timezone.utc).isoformat()}, indent=2))
    _log.info("retrain report: %s", out)
    return 0 if all(rc == 0 for rc in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
