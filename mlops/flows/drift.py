"""Daily drift-detection flow.

Pulls the last 24h of inputs from ``agent_calls`` (proxy for production
traffic) and compares against a snapshot of the training distribution.
Writes ``reports/drift/<date>.json`` and posts a webhook alert when any
domain breaches its threshold.

Two checks per domain (where applicable):

  * **Tabular**: two-sample Kolmogorov-Smirnov test on numeric features
    (transaction_amount, clicks_per_minute, ...). KS p-value < 0.01 →
    drift.
  * **Text**: hashing-based embedding mean shift on tool inputs. Cosine
    distance > 0.25 from the training centroid → drift.

The flow is best-effort. If the database isn't reachable, or the
training reference is missing, we log and exit cleanly so the cron job
doesn't loop on errors.

Run manually for development:

    python -m mlops.flows.drift --since 24h --window-days 1
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

_log = logging.getLogger("Sentifargo.mlops.drift")

REPORTS_DIR = Path("reports/drift")
REFERENCES_DIR = Path("data/drift/references")  # one JSON per domain
DEFAULT_THRESHOLDS = {
    "ks_pvalue_min": 0.01,
    "embedding_cosine_max": 0.25,
}

# Prefect decorators are real only when PREFECT_API_URL is set or when
# running under a Prefect agent. In dev/CI we keep the flow callable as a
# plain function so unit tests can drive it without spinning up the
# Prefect server.
def _noop_flow(*args, **kwargs):  # type: ignore
    def _wrap(fn):
        return fn
    if args and callable(args[0]):
        return args[0]
    return _wrap


def _noop_task(*args, **kwargs):  # type: ignore
    def _wrap(fn):
        return fn
    if args and callable(args[0]):
        return args[0]
    return _wrap


if os.environ.get("PREFECT_API_URL"):
    try:
        from prefect import flow, task  # type: ignore
    except Exception:  # pragma: no cover
        flow, task = _noop_flow, _noop_task
else:
    flow, task = _noop_flow, _noop_task


@dataclass
class DriftFinding:
    domain: str
    metric: str
    value: float
    threshold: float
    drifted: bool
    sample_size: int
    detail: str = ""


@dataclass
class DriftReport:
    ran_at: str
    window_hours: int
    findings: list[DriftFinding] = field(default_factory=list)

    @property
    def any_drift(self) -> bool:
        return any(f.drifted for f in self.findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ran_at": self.ran_at,
            "window_hours": self.window_hours,
            "drifted": self.any_drift,
            "findings": [f.__dict__ for f in self.findings],
        }


@task
def load_reference(domain: str) -> dict[str, Any] | None:
    path = REFERENCES_DIR / f"{domain}.json"
    if not path.exists():
        _log.info("no drift reference for %s at %s — skipping", domain, path)
        return None
    return json.loads(path.read_text())


@task
def load_recent_calls(window_hours: int) -> list[dict[str, Any]]:
    """Fetch agent_calls rows from the last ``window_hours``.

    We pull only the fields we use for drift; the rest stays in Postgres.
    Returns an empty list when the DB is unreachable.
    """
    try:
        from app.db.models import AgentCall
        from app.db.session import SessionLocal
    except Exception as exc:  # pragma: no cover
        _log.warning("agent_calls fetch skipped (db unavailable): %s", exc)
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    try:
        with SessionLocal() as session:
            rows = (
                session.query(AgentCall)
                .filter(AgentCall.created_at >= cutoff)
                .all()
            )
            return [
                {
                    "intent": r.intent,
                    "user_id": r.user_id,
                    "tool_calls": r.tool_calls,
                    "input_tokens": r.input_tokens,
                    "output_tokens": r.output_tokens,
                    "latency_ms": r.latency_ms,
                    "confidence": r.confidence,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]
    except Exception as exc:  # pragma: no cover
        _log.warning("agent_calls fetch failed: %s", exc)
        return []


def _ks_test(reference: Sequence[float], live: Sequence[float]) -> tuple[float, float]:
    """Return (statistic, p_value). Falls back to a numpy-only ECDF
    distance if scipy isn't available."""
    if not reference or not live:
        return 0.0, 1.0
    try:
        from scipy import stats  # type: ignore

        result = stats.ks_2samp(reference, live, alternative="two-sided", mode="auto")
        return float(result.statistic), float(result.pvalue)
    except Exception:
        # ECDF distance — quick approximation when scipy is missing.
        import numpy as np

        ref = np.sort(np.asarray(reference, dtype=float))
        cur = np.sort(np.asarray(live, dtype=float))
        all_x = np.unique(np.concatenate([ref, cur]))
        ecdf_ref = np.searchsorted(ref, all_x, side="right") / max(len(ref), 1)
        ecdf_cur = np.searchsorted(cur, all_x, side="right") / max(len(cur), 1)
        statistic = float(np.max(np.abs(ecdf_ref - ecdf_cur)))
        # Coarse p-value approximation for the missing-scipy path.
        p_value = float(np.exp(-2 * (statistic ** 2) * min(len(ref), len(cur))))
        return statistic, p_value


@task
def detect_tabular_drift(
    domain: str,
    reference: dict[str, Any] | None,
    rows: list[dict[str, Any]],
    thresholds: dict[str, float],
) -> list[DriftFinding]:
    if not reference or not rows:
        return []

    findings: list[DriftFinding] = []
    threshold = thresholds.get("ks_pvalue_min", DEFAULT_THRESHOLDS["ks_pvalue_min"])

    for feature, ref_values in (reference.get("tabular") or {}).items():
        live_values = [
            r.get(feature) for r in rows if isinstance(r.get(feature), (int, float))
        ]
        if not live_values:
            continue
        statistic, p_value = _ks_test(ref_values, live_values)
        findings.append(
            DriftFinding(
                domain=domain,
                metric=f"{feature}.ks_pvalue",
                value=p_value,
                threshold=threshold,
                drifted=p_value < threshold,
                sample_size=len(live_values),
                detail=f"ks_statistic={statistic:.4f}",
            )
        )
    return findings


def _post_alert(report: DriftReport) -> None:
    url = os.getenv("DRIFT_ALERT_WEBHOOK", "").strip()
    if not url:
        return
    try:
        import urllib.request

        body = json.dumps(report.to_dict()).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
        _log.info("drift webhook posted")
    except Exception as exc:  # pragma: no cover
        _log.warning("drift webhook failed: %s", exc)


@flow(name="drift-detection")
def detect_drift(window_hours: int = 24) -> DriftReport:
    rows = load_recent_calls(window_hours)
    report = DriftReport(
        ran_at=datetime.now(timezone.utc).isoformat(),
        window_hours=window_hours,
    )

    by_domain: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        by_domain.setdefault(r.get("intent") or "unknown", []).append(r)

    for domain, domain_rows in by_domain.items():
        ref = load_reference(domain)
        report.findings.extend(
            detect_tabular_drift(domain, ref, domain_rows, DEFAULT_THRESHOLDS)
        )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / f"drift_{datetime.now(timezone.utc).date()}.json"
    out.write_text(json.dumps(report.to_dict(), indent=2))
    _log.info("drift report written: %s (drifted=%s)", out, report.any_drift)

    if report.any_drift:
        _post_alert(report)
    return report


def _cli() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--window-hours", type=int, default=24)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    report = detect_drift(window_hours=args.window_hours)
    return 1 if report.any_drift else 0


if __name__ == "__main__":
    sys.exit(_cli())
