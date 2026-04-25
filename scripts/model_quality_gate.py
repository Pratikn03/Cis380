#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "artifacts" / "release" / "model-manifest.json"
DEFAULT_REPORT_JSON = ROOT / "reports" / "MODEL_QUALITY_GATE.json"
DEFAULT_REPORT_MD = ROOT / "reports" / "MODEL_QUALITY_GATE.md"


THRESHOLDS: dict[str, list[dict[str, Any]]] = {
    "fraud": [
        {"metric": "roc_auc", "op": ">=", "value": 0.90},
        {"metric": "pr_auc", "op": ">=", "value": 0.60},
        {"metric": "f1", "op": ">=", "value": 0.65},
    ],
    "cyber": [
        {"metric": "roc_auc", "op": ">=", "value": 0.98},
        {"metric": "f1", "op": ">=", "value": 0.94},
    ],
    "behavior": [
        {"metric": "roc_auc", "op": ">=", "value": 0.75},
        {"metric": "f1", "op": ">=", "value": 0.45},
        {"metric": "fpr", "op": "<=", "value": 0.05},
    ],
    "vision_deepfake": [
        {"metric": "roc_auc", "op": ">=", "value": 0.90},
        {"metric": "f1", "op": ">=", "value": 0.80},
        {"metric": "accuracy", "op": ">=", "value": 0.85},
    ],
    "vision_face_emotion": [
        {
            "any": [
                {"metric": "macro_f1", "op": ">=", "value": 0.55},
                {"metric": "balanced_accuracy", "op": ">=", "value": 0.60},
            ]
        }
    ],
    "vision_temporal": [{"metric": "val_accuracy", "op": ">=", "value": 0.75}],
    "brand": [
        {"metric": "map50", "op": ">=", "value": 0.50},
        {"metric": "smoke_inference", "op": "==", "value": "pass"},
    ],
    "voice": [
        {"metric": "macro_f1", "op": ">=", "value": 0.60},
        {"metric": "balanced_accuracy", "op": ">=", "value": 0.60},
    ],
    "recommender": [
        {"metric": "macro_f1", "op": ">=", "value": 0.70},
        {"metric": "precision_at_5", "op": ">=", "value": 0.20},
    ],
    "fusion": [
        {"metric": "roc_auc", "op": ">=", "value": 0.90},
        {"metric": "f1", "op": ">=", "value": 0.70},
    ],
    "rag": [
        {"metric": "mrr", "op": ">=", "value": 0.70},
        {"metric": "citation_coverage", "op": ">=", "value": 0.90},
    ],
}


ALIASES: dict[str, tuple[str, ...]] = {
    "roc_auc": ("roc_auc", "auc", "auroc"),
    "pr_auc": ("pr_auc", "average_precision"),
    "f1": ("f1", "f1_score", "macro_avg_f1_score"),
    "fpr": ("fpr", "false_positive_rate", "autoencoder_fpr"),
    "accuracy": ("accuracy", "acc", "val_accuracy", "best_val_acc"),
    "val_accuracy": ("val_accuracy",),
    "macro_f1": ("macro_f1", "macro_avg_f1_score", "f1_macro"),
    "balanced_accuracy": ("balanced_accuracy", "balanced_acc"),
    "map50": ("map50", "metrics_map50_b"),
    "precision_at_5": ("precision_at_5", "precision_5", "precision_at_k_5"),
    "mrr": ("mrr",),
    "citation_coverage": ("citation_coverage", "citation_coverage_at_k"),
}


def _normalize_key(raw: str) -> str:
    key = re.sub(r"[^a-zA-Z0-9]+", "_", raw.strip().lower()).strip("_")
    key = key.replace("m_ap50", "map50")
    return key


def _flatten(payload: Any, prefix: str = "") -> dict[str, float]:
    values: dict[str, float] = {}
    if isinstance(payload, dict):
        for raw_key, raw_value in payload.items():
            key = _normalize_key(str(raw_key))
            joined = f"{prefix}_{key}" if prefix else key
            values.update(_flatten(raw_value, joined))
    elif isinstance(payload, list):
        for idx, raw_value in enumerate(payload):
            values.update(_flatten(raw_value, f"{prefix}_{idx}" if prefix else str(idx)))
    else:
        try:
            values[prefix] = float(payload)
        except (TypeError, ValueError):
            pass
    return values


def _read_metrics(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            return {}
        if {"Metric", "Value"}.issubset(rows[0].keys()):
            return {
                _normalize_key(str(row["Metric"])): float(row["Value"])
                for row in rows
                if str(row.get("Value", "")).strip()
            }
        return _flatten(rows[-1])
    return _flatten(json.loads(path.read_text(encoding="utf-8")))


def _metric_value(values: dict[str, float], metric: str) -> float | None:
    aliases = ALIASES.get(metric, (metric,))
    preferred_test: list[float] = []
    hits: list[float] = []
    for key, value in values.items():
        for alias in aliases:
            if key == alias or key.endswith(f"_{alias}"):
                hits.append(value)
                if key.startswith("test_") or "_test_" in key:
                    preferred_test.append(value)
                break
    if preferred_test:
        return max(preferred_test)
    if hits:
        return max(hits)
    return None


def _compare(actual: Any, op: str, expected: Any) -> bool:
    if actual is None:
        return False
    if op == "==":
        return str(actual).lower() == str(expected).lower()
    try:
        actual_float = float(actual)
        expected_float = float(expected)
    except (TypeError, ValueError):
        return False
    if op == ">=":
        return actual_float >= expected_float
    if op == "<=":
        return actual_float <= expected_float
    raise ValueError(f"Unsupported operator: {op}")


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _evaluate_rule(rule: dict[str, Any], values: dict[str, float], smoke: str) -> dict[str, Any]:
    if "any" in rule:
        children = [_evaluate_rule(child, values, smoke) for child in rule["any"]]
        return {
            "rule": "any",
            "passed": any(child["passed"] for child in children),
            "children": children,
        }

    metric = str(rule["metric"])
    actual: Any = smoke if metric == "smoke_inference" else _metric_value(values, metric)
    passed = _compare(actual, str(rule["op"]), rule["value"])
    return {
        "metric": metric,
        "operator": rule["op"],
        "expected": rule["value"],
        "actual": actual,
        "passed": passed,
    }


def _model_result(entry: dict[str, Any], *, verify_sha: bool) -> dict[str, Any]:
    domain = str(entry.get("domain", "")).strip()
    artifact_path = ROOT / str(entry.get("path", ""))
    metrics_path = ROOT / str(entry.get("metricsFile", ""))
    values = _read_metrics(metrics_path)
    rules = THRESHOLDS.get(domain, [])
    smoke = str(entry.get("smokeInference", "")).lower()
    rule_results = [_evaluate_rule(rule, values, smoke) for rule in rules]
    failures = [rule for rule in rule_results if not rule["passed"]]

    sha_status = "skipped"
    if verify_sha:
        expected_sha = str(entry.get("artifactSha256", "")).strip()
        if not artifact_path.exists():
            sha_status = "missing"
            failures.append(
                {"metric": "artifact_exists", "passed": False, "path": str(artifact_path)}
            )
        elif expected_sha and _sha256(artifact_path) != expected_sha:
            sha_status = "mismatch"
            failures.append({"metric": "artifact_sha256", "passed": False})
        else:
            sha_status = "ok"

    return {
        "domain": domain,
        "modelName": entry.get("modelName"),
        "artifact": entry.get("path"),
        "metricsFile": entry.get("metricsFile"),
        "qualityStatus": "pass" if not failures else "fail",
        "thresholds": rules,
        "metricFailures": failures,
        "artifactSha256Status": sha_status,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate strict production model quality gates.")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--report-json", default=str(DEFAULT_REPORT_JSON))
    parser.add_argument("--report-md", default=str(DEFAULT_REPORT_MD))
    parser.add_argument("--skip-sha", action="store_true")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    results = [
        _model_result(entry, verify_sha=not args.skip_sha)
        for entry in payload.get("models", [])
        if isinstance(entry, dict)
    ]
    missing_domains = sorted(set(THRESHOLDS) - {result["domain"] for result in results})
    failed = [result for result in results if result["qualityStatus"] != "pass"]
    status = "pass" if not failed and not missing_domains else "fail"

    report = {
        "status": status,
        "manifest": str(manifest_path),
        "missingDomains": missing_domains,
        "results": results,
    }
    report_json = Path(args.report_json)
    report_md = Path(args.report_md)
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = ["# Model Quality Gate", "", f"- Status: **{status}**", ""]
    if missing_domains:
        lines.append(f"- Missing domains: {', '.join(missing_domains)}")
        lines.append("")
    for result in results:
        lines.append(f"## {result['domain']}")
        lines.append(f"- Status: **{result['qualityStatus']}**")
        lines.append(f"- Artifact: `{result['artifact']}`")
        lines.append(f"- Metrics: `{result['metricsFile']}`")
        if result["metricFailures"]:
            lines.append(f"- Failures: `{json.dumps(result['metricFailures'])}`")
        lines.append("")
    report_md.write_text("\n".join(lines), encoding="utf-8")

    if status != "pass":
        print(f"Model quality gate failed. Wrote {report_md} and {report_json}")
        return 1
    print(f"Model quality gate passed. Wrote {report_md} and {report_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
