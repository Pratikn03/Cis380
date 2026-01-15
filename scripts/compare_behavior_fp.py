from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], *, env: dict[str, str]) -> None:
    result = subprocess.run(cmd, env=env, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fpr(metrics: dict, key: str) -> float:
    return float(metrics.get(f"{key}_fpr", 0.0))


def _cm(metrics: dict, key: str) -> dict:
    return metrics.get(f"{key}_confusion", {})


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_md(path: Path, baseline: dict, augmented: dict, delta: dict) -> None:
    lines = [
        "# Behavior False-Positive Comparison",
        "",
        "## Autoencoder",
        "",
        "| Metric | Baseline | Augmented | Delta |",
        "| --- | --- | --- | --- |",
        f"| FPR | {baseline['autoencoder_fpr']:.4f} | {augmented['autoencoder_fpr']:.4f} | {delta['autoencoder_fpr']:+.4f} |",
        "",
        "Baseline confusion: " + json.dumps(baseline["autoencoder_confusion"]),
        "",
        "Augmented confusion: " + json.dumps(augmented["autoencoder_confusion"]),
        "",
        "## LOF",
        "",
        "| Metric | Baseline | Augmented | Delta |",
        "| --- | --- | --- | --- |",
        f"| FPR | {baseline['lof_fpr']:.4f} | {augmented['lof_fpr']:.4f} | {delta['lof_fpr']:+.4f} |",
        "",
        "Baseline confusion: " + json.dumps(baseline["lof_confusion"]),
        "",
        "Augmented confusion: " + json.dumps(augmented["lof_confusion"]),
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Compare behavior false-positive rates before/after augmentation.")
    ap.add_argument("--reports-dir", default="reports")
    ap.add_argument("--metrics-dir", default="experiments/behavior/metrics")
    ap.add_argument(
        "--data-path",
        default="data/raw/behavior/online_shoppers_intention.csv",
        help="Behavior dataset path for baseline/augmented runs.",
    )
    ap.add_argument(
        "--baseline-insider-ratio",
        type=float,
        default=0.01,
        help="Small insider injection for baseline so positives exist.",
    )
    ap.add_argument(
        "--augmented-insider-ratio",
        type=float,
        default=0.05,
        help="Insider injection ratio for augmented run.",
    )
    ap.add_argument("--use-existing", action="store_true", help="Skip retraining; reuse existing metrics files.")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    metrics_dir = repo_root / args.metrics_dir
    reports_dir = repo_root / args.reports_dir
    baseline_path = metrics_dir / "baseline_metrics.json"
    augmented_path = metrics_dir / "augmented_metrics.json"

    if not args.use_existing:
        env = os.environ.copy()
        env.update(
            {
                "BEHAVIOR_AUGMENT_INSIDER": "true",
                "BEHAVIOR_INSIDER_RATIO": str(args.baseline_insider_ratio),
                "BEHAVIOR_DATA_PATH": args.data_path,
                "BEHAVIOR_METRICS_PATH": str(baseline_path),
                "BEHAVIOR_SCORES_PATH": str(metrics_dir / "baseline_scores.csv"),
                "BEHAVIOR_RUN_TAG": "baseline_seeded",
            }
        )
        _run([sys.executable, "src/scripts/run_behavior_experiment.py"], env=env)

        env = os.environ.copy()
        env.update(
            {
                "BEHAVIOR_AUGMENT_INSIDER": "true",
                "BEHAVIOR_INSIDER_RATIO": str(args.augmented_insider_ratio),
                "BEHAVIOR_DATA_PATH": args.data_path,
                "BEHAVIOR_METRICS_PATH": str(augmented_path),
                "BEHAVIOR_SCORES_PATH": str(metrics_dir / "augmented_scores.csv"),
                "BEHAVIOR_RUN_TAG": "augmented",
            }
        )
        _run([sys.executable, "src/scripts/run_behavior_experiment.py"], env=env)

    if not baseline_path.exists() or not augmented_path.exists():
        raise SystemExit(
            f"Missing metrics. baseline={baseline_path.exists()} augmented={augmented_path.exists()}"
        )

    baseline = _load_json(baseline_path)
    augmented = _load_json(augmented_path)

    delta = {
        "autoencoder_fpr": _fpr(augmented, "autoencoder") - _fpr(baseline, "autoencoder"),
        "lof_fpr": _fpr(augmented, "lof") - _fpr(baseline, "lof"),
    }

    snapshot_path = reports_dir / "behavior_baseline_snapshot.json"
    _write_json(snapshot_path, baseline)

    confusion_report = {
        "baseline": {
            "autoencoder_confusion": _cm(baseline, "autoencoder"),
            "lof_confusion": _cm(baseline, "lof"),
        },
        "augmented": {
            "autoencoder_confusion": _cm(augmented, "autoencoder"),
            "lof_confusion": _cm(augmented, "lof"),
        },
    }
    confusion_path = reports_dir / "behavior_confusion_report.json"
    _write_json(confusion_path, confusion_report)

    delta_path = reports_dir / "behavior_fp_delta.json"
    _write_json(delta_path, delta)

    md_path = reports_dir / "behavior_fp_delta.md"
    _write_md(
        md_path,
        {
            "autoencoder_fpr": _fpr(baseline, "autoencoder"),
            "lof_fpr": _fpr(baseline, "lof"),
            "autoencoder_confusion": _cm(baseline, "autoencoder"),
            "lof_confusion": _cm(baseline, "lof"),
        },
        {
            "autoencoder_fpr": _fpr(augmented, "autoencoder"),
            "lof_fpr": _fpr(augmented, "lof"),
            "autoencoder_confusion": _cm(augmented, "autoencoder"),
            "lof_confusion": _cm(augmented, "lof"),
        },
        delta,
    )

    print(f"Wrote baseline snapshot: {snapshot_path}")
    print(f"Wrote confusion report: {confusion_path}")
    print(f"Wrote delta report: {delta_path}")
    print(f"Wrote delta markdown: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
