#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = ROOT / "reports"

CATALOG_SCRIPT = ROOT / "scripts" / "data" / "validate_catalog.py"
DATASET_SCRIPT = ROOT / "scripts" / "data" / "validate_dataset.py"
SPLITS_SCRIPT = ROOT / "scripts" / "data" / "make_splits.py"
TRAINING_AUDIT_SCRIPT = ROOT / "scripts" / "training_data_audit.py"


@dataclass
class GateResult:
    name: str
    status: str
    details: str


DATASET_CHECKS = [
    ("tabular", "fraud", ROOT / "data" / "raw" / "fraud" / "creditcard.csv"),
    ("tabular", "cyber", ROOT / "data" / "raw" / "cyber" / "UNSW_NB15_training-set.csv"),
    ("tabular", "behavior", ROOT / "data" / "raw" / "behavior" / "online_shoppers_intention.csv"),
    ("audio", "voice", ROOT / "data" / "raw" / "voice"),
    ("vision", "brand", ROOT / "data" / "processed" / "brand_yolo"),
]


def _run(cmd: list[str], cwd: Path = ROOT) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return proc.returncode, proc.stdout.strip()


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(8192)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _null_duplicate_ratio(csv_path: Path) -> dict[str, Any]:
    frame = pd.read_csv(csv_path)
    total_rows = len(frame)
    total_cells = int(frame.shape[0] * frame.shape[1]) if frame.shape[1] else 0
    null_count = int(frame.isna().sum().sum())
    duplicate_count = int(frame.duplicated().sum())
    null_pct = (null_count / total_cells * 100.0) if total_cells else 0.0
    duplicate_pct = (duplicate_count / total_rows * 100.0) if total_rows else 0.0

    label_col = None
    for candidate in ("label", "class", "isFraud", "isfraud", "target", "Revenue"):
        if candidate in frame.columns:
            label_col = candidate
            break
    imbalance = None
    if label_col is not None and total_rows:
        vc = frame[label_col].value_counts(normalize=True, dropna=False)
        if not vc.empty:
            imbalance = float(vc.max())

    return {
        "rows": total_rows,
        "columns": int(frame.shape[1]),
        "null_pct": round(null_pct, 3),
        "duplicate_pct": round(duplicate_pct, 3),
        "label_column": label_col,
        "majority_class_pct": round(imbalance, 4) if imbalance is not None else None,
    }


def run_quality_gates(catalog_path: Path, strict_data_presence: bool) -> int:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    results: list[GateResult] = []
    failures = 0

    # 1) Catalog validation
    code, output = _run([sys.executable, str(CATALOG_SCRIPT), "--catalog", str(catalog_path), "--strict"])
    if code != 0:
        failures += 1
        results.append(GateResult("catalog", "fail", output))
    else:
        results.append(GateResult("catalog", "pass", output))

    # 2) Dataset format checks
    for task, dataset, path in DATASET_CHECKS:
        if not path.exists():
            status = "fail" if strict_data_presence else "warn"
            if status == "fail":
                failures += 1
            results.append(
                GateResult(
                    f"dataset:{task}:{dataset}",
                    status,
                    f"missing path: {path}",
                )
            )
            continue

        code, output = _run(
            [
                sys.executable,
                str(DATASET_SCRIPT),
                "--task",
                task,
                "--dataset",
                dataset,
                "--path",
                str(path),
            ]
        )
        if code != 0:
            failures += 1
            results.append(GateResult(f"dataset:{task}:{dataset}", "fail", output))
        else:
            results.append(GateResult(f"dataset:{task}:{dataset}", "pass", output))

    # 3) Split determinism on synthetic tabular data
    with tempfile.TemporaryDirectory(prefix="sentifargo-quality-") as tmpdir:
        tmp = Path(tmpdir)
        csv_path = tmp / "sample.csv"
        df = pd.DataFrame(
            {
                "feature_a": list(range(1, 31)),
                "feature_b": [x * 1.5 for x in range(1, 31)],
                "label": [0 if x % 3 else 1 for x in range(1, 31)],
            }
        )
        df.to_csv(csv_path, index=False)

        out_a = tmp / "split_a"
        out_b = tmp / "split_b"
        out_a.mkdir(parents=True, exist_ok=True)
        out_b.mkdir(parents=True, exist_ok=True)

        args = [
            sys.executable,
            str(SPLITS_SCRIPT),
            "--task",
            "tabular",
            "--dataset",
            "quality_fixture",
            "--seed",
            "123",
            "--train",
            "0.7",
            "--val",
            "0.2",
            "--test",
            "0.1",
            "--path",
            str(csv_path),
        ]

        code_a, out_text_a = _run(args, cwd=tmp)
        code_b, out_text_b = _run(args, cwd=tmp)
        if code_a != 0 or code_b != 0:
            failures += 1
            results.append(
                GateResult(
                    "split_determinism",
                    "fail",
                    f"split generation failed:\n{out_text_a}\n{out_text_b}",
                )
            )
        else:
            split_path = tmp / "data" / "splits" / "tabular" / "quality_fixture" / "splits.json"
            hash_a = _hash_file(split_path)
            # Re-run to ensure deterministic output for same seed/input.
            code_c, out_text_c = _run(args, cwd=tmp)
            hash_b = _hash_file(split_path)
            if code_c != 0 or hash_a != hash_b:
                failures += 1
                results.append(
                    GateResult(
                        "split_determinism",
                        "fail",
                        f"determinism mismatch hash_a={hash_a} hash_b={hash_b}\n{out_text_c}",
                    )
                )
            else:
                results.append(
                    GateResult(
                        "split_determinism",
                        "pass",
                        f"deterministic hash={hash_a}",
                    )
                )

    # 4) Hygiene metrics on available tabular datasets
    hygiene_rows = []
    for _, dataset, path in DATASET_CHECKS:
        if path.suffix.lower() != ".csv" or not path.exists():
            continue
        try:
            metrics = _null_duplicate_ratio(path)
            hygiene_rows.append({"dataset": dataset, "path": str(path), **metrics})
        except Exception as exc:  # pragma: no cover - defensive
            failures += 1
            results.append(GateResult(f"hygiene:{dataset}", "fail", f"{path}: {exc}"))

    for row in hygiene_rows:
        status = "pass"
        details = (
            f"rows={row['rows']} null_pct={row['null_pct']} duplicate_pct={row['duplicate_pct']} "
            f"majority_class_pct={row['majority_class_pct']}"
        )
        if row["null_pct"] > 25.0 or row["duplicate_pct"] > 20.0:
            status = "fail"
        if row["majority_class_pct"] is not None and row["majority_class_pct"] > 0.995:
            status = "fail"
        if status == "fail":
            failures += 1
        results.append(GateResult(f"hygiene:{row['dataset']}", status, details))

    # 5) Training data audit reports
    code, output = _run([sys.executable, str(TRAINING_AUDIT_SCRIPT)])
    if code != 0:
        failures += 1
        results.append(GateResult("training_data_audit", "fail", output))
    else:
        md = ROOT / "reports" / "TRAINING_DATA.md"
        js = ROOT / "reports" / "TRAINING_DATA.json"
        if not md.exists() or not js.exists():
            failures += 1
            results.append(
                GateResult(
                    "training_data_audit",
                    "fail",
                    "audit script ran but expected reports/TRAINING_DATA.{md,json} were not found",
                )
            )
        else:
            results.append(GateResult("training_data_audit", "pass", output))

    payload = {
        "status": "pass" if failures == 0 else "fail",
        "failures": failures,
        "strict_data_presence": strict_data_presence,
        "results": [asdict(r) for r in results],
    }
    (REPORTS_DIR / "data_quality_gate.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_lines = [
        "# Data Quality Gate",
        "",
        f"- status: **{payload['status']}**",
        f"- failures: {payload['failures']}",
        f"- strict_data_presence: {payload['strict_data_presence']}",
        "",
        "## Checks",
    ]
    for item in payload["results"]:
        md_lines.append(f"- `{item['name']}`: **{item['status']}**")
        md_lines.append(f"  - {item['details']}")
    (REPORTS_DIR / "data_quality_gate.md").write_text("\n".join(md_lines), encoding="utf-8")

    print(json.dumps(payload, indent=2))
    return 0 if failures == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Sentifargo data quality gates.")
    parser.add_argument(
        "--catalog",
        default=str(ROOT / "data" / "catalogs" / "datasets.yaml"),
        help="Path to data catalog YAML file.",
    )
    parser.add_argument(
        "--strict-data-presence",
        action="store_true",
        help="Fail when required dataset paths are missing.",
    )
    args = parser.parse_args()
    return run_quality_gates(Path(args.catalog), strict_data_presence=args.strict_data_presence)


if __name__ == "__main__":
    raise SystemExit(main())
