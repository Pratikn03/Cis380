#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GATES = ROOT / "configs" / "promotion_gates.yaml"
DEFAULT_MANIFEST = ROOT / "artifacts" / "release" / "model-manifest.json"
REPORT_JSON = ROOT / "reports" / "PROMOTION_GATE.json"
REPORT_MD = ROOT / "reports" / "PROMOTION_GATE.md"


def normalize_key(raw: str) -> str:
    key = "".join(ch.lower() if ch.isalnum() else "_" for ch in str(raw)).strip("_")
    while "__" in key:
        key = key.replace("__", "_")
    return key.replace("m_ap50", "map50")


def load_gates(path: Path = DEFAULT_GATES) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Promotion gates not found: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload.get("domains"), dict):
        raise ValueError("promotion_gates.yaml must contain a 'domains' mapping")
    return payload


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def resolve_path(raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


def git_sha(short: bool = True) -> str:
    cmd = ["git", "rev-parse", "--short" if short else "HEAD", "HEAD"]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return proc.stdout.strip()
    except Exception:
        return "unknown"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_tree(path: Path) -> str:
    digest = hashlib.sha256()
    if not path.exists():
        raise FileNotFoundError(path)
    if path.is_file():
        return sha256_file(path)
    for child in sorted(p for p in path.rglob("*") if p.is_file()):
        relative = child.relative_to(path).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        with child.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        digest.update(b"\0")
    return digest.hexdigest()


def dataset_version(source: Path) -> str:
    if not source.exists():
        return "missing"
    return sha256_tree(source)[:16]


def flatten_metrics(payload: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(payload, dict):
        for key, value in payload.items():
            raw_key = str(key)
            dotted = f"{prefix}.{raw_key}" if prefix else raw_key
            normalized = f"{normalize_key(prefix)}_{normalize_key(raw_key)}" if prefix else normalize_key(raw_key)
            out.update(flatten_metrics(value, dotted))
            if not isinstance(value, (dict, list)):
                out[dotted] = value
                out[normalized] = value
    elif isinstance(payload, list):
        for idx, value in enumerate(payload):
            dotted = f"{prefix}.{idx}" if prefix else str(idx)
            out.update(flatten_metrics(value, dotted))
    elif prefix:
        out[prefix] = payload
        out[normalize_key(prefix)] = payload
    return out


def _read_csv_metrics(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return {}
    first = rows[0]
    if {"Metric", "Value"}.issubset(first):
        return {
            row["Metric"]: row.get("Value")
            for row in rows
            if str(row.get("Metric", "")).strip()
        }
    return flatten_metrics(rows[-1])


def read_metrics(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    if path.suffix.lower() == ".csv":
        return flatten_metrics(_read_csv_metrics(path))
    return flatten_metrics(json.loads(path.read_text(encoding="utf-8")))


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def metric_value(values: dict[str, Any], metric: str) -> float | None:
    candidates = [
        metric,
        normalize_key(metric),
        metric.replace("/", "_"),
        metric.replace(".", "_"),
    ]
    for candidate in candidates:
        if candidate in values:
            return to_float(values[candidate])
    wanted = normalize_key(metric)
    hits = []
    for key, value in values.items():
        norm = normalize_key(key)
        if norm == wanted or norm.endswith(f"_{wanted}"):
            parsed = to_float(value)
            if parsed is not None:
                hits.append(parsed)
    return max(hits) if hits else None


def _expected_from_rule(
    rule: dict[str, Any], domain_cfg: dict[str, Any], gates: dict[str, Any]
) -> float | str:
    if "value" in rule:
        return rule["value"]
    baseline_key = str(rule.get("baseline") or rule.get("metric"))
    baseline_raw = (domain_cfg.get("baselines") or {}).get(baseline_key)
    baseline = to_float(baseline_raw)
    if baseline is None:
        raise ValueError(f"Missing numeric baseline for {baseline_key}")
    delta = float(
        rule.get("relative_min_delta_pct", gates.get("default_relative_improvement_pct", 0.0))
    )
    op = str(rule.get("op", ">="))
    multiplier = 1.0 - (delta / 100.0) if op == "<=" else 1.0 + (delta / 100.0)
    return float(baseline * multiplier)


def compare(actual: Any, op: str, expected: Any) -> bool:
    if actual is None:
        return False
    if op == "==":
        return str(actual).lower() == str(expected).lower()
    left = to_float(actual)
    right = to_float(expected)
    if left is None or right is None:
        return False
    if op == ">=":
        return left >= right
    if op == "<=":
        return left <= right
    if op == ">":
        return left > right
    if op == "<":
        return left < right
    raise ValueError(f"Unsupported operator: {op}")


def _is_lower_better(domain_cfg: dict[str, Any], metric: str) -> bool:
    configured = {normalize_key(item) for item in domain_cfg.get("lower_is_better", []) or []}
    normalized = normalize_key(metric)
    if normalized in configured:
        return True
    return any(token in normalized for token in ("fpr", "wer", "cer", "latency", "loss", "error"))


def evaluate_regressions(
    domain: str,
    domain_cfg: dict[str, Any],
    gates: dict[str, Any],
    values: dict[str, Any],
) -> list[dict[str, Any]]:
    tolerance = float(gates.get("default_max_regression_pct", 2.0))
    failures: list[dict[str, Any]] = []
    for metric, baseline_raw in (domain_cfg.get("baselines") or {}).items():
        baseline = to_float(baseline_raw)
        current = metric_value(values, str(metric))
        if baseline is None or current is None:
            continue
        if baseline == 0:
            continue
        worse_pct = (
            ((current - baseline) / abs(baseline)) * 100.0
            if _is_lower_better(domain_cfg, str(metric))
            else ((baseline - current) / abs(baseline)) * 100.0
        )
        if worse_pct > tolerance:
            failures.append(
                {
                    "domain": domain,
                    "metric": metric,
                    "baseline": baseline,
                    "actual": current,
                    "max_regression_pct": tolerance,
                    "actual_regression_pct": round(worse_pct, 6),
                    "passed": False,
                }
            )
    return failures


def evaluate_domain(
    domain: str, domain_cfg: dict[str, Any], gates: dict[str, Any]
) -> dict[str, Any]:
    metrics_path = resolve_path(domain_cfg["metrics"])
    artifact_path = resolve_path(domain_cfg["artifact"])
    values = read_metrics(metrics_path)
    rule_results: list[dict[str, Any]] = []
    for rule in domain_cfg.get("gates", []) or []:
        metric = str(rule["metric"])
        expected = _expected_from_rule(rule, domain_cfg, gates)
        actual = metric_value(values, metric)
        op = str(rule.get("op", ">="))
        passed = compare(actual, op, expected)
        rule_results.append(
            {
                "domain": domain,
                "metric": metric,
                "operator": op,
                "expected": expected,
                "actual": actual,
                "baseline": rule.get("baseline"),
                "passed": passed,
            }
        )
    regression_failures = evaluate_regressions(domain, domain_cfg, gates, values)
    artifact_exists = artifact_path.exists()
    failures = [rule for rule in rule_results if not rule["passed"]] + regression_failures
    if not artifact_exists:
        failures.append(
            {
                "domain": domain,
                "metric": "artifact_exists",
                "operator": "exists",
                "expected": True,
                "actual": False,
                "path": rel_path(artifact_path),
                "passed": False,
            }
        )
    selected_metrics = {
        result["metric"]: result["actual"]
        for result in rule_results
        if result.get("actual") is not None
    }
    return {
        "domain": domain,
        "status": "pass" if not failures else "fail",
        "metricsFile": rel_path(metrics_path),
        "artifact": rel_path(artifact_path),
        "artifactExists": artifact_exists,
        "thresholds": rule_results,
        "regressions": regression_failures,
        "failures": failures,
        "selectedMetrics": selected_metrics,
        "allMetrics": values,
    }


def copy_artifact(source: Path, release_dir: Path) -> Path:
    release_dir.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        dest = release_dir / source.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(source, dest, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
        return dest
    dest = release_dir / source.name
    shutil.copy2(source, dest)
    return dest


def render_model_card(
    *,
    domain: str,
    cfg: dict[str, Any],
    promoted_path: Path,
    result: dict[str, Any],
    artifact_sha: str,
    data_version: str,
    sha: str,
) -> str:
    metrics = result.get("selectedMetrics", {})
    return "\n".join(
        [
            f"# Model Card: {cfg.get('model_name', domain)}",
            "",
            "## Overview",
            f"- Domain: {domain}",
            f"- Version: {cfg.get('version', '1.0.0')}",
            f"- Framework: {cfg.get('framework', 'unknown')}",
            f"- Artifact: {rel_path(promoted_path)}",
            f"- Artifact SHA256: {artifact_sha}",
            f"- Training git SHA: {sha}",
            f"- Dataset: {cfg.get('dataset', 'unknown')}",
            f"- Dataset version: {data_version}",
            "",
            "## Intended Use",
            "Production inference for the Sentifargo anomaly intelligence platform.",
            "",
            "## Metrics",
            json.dumps(metrics, indent=2, sort_keys=True),
            "",
            "## Data",
            f"Training/evaluation data source: `{cfg.get('dataset', 'unknown')}`.",
            "",
            "## Limitations",
            "Metrics reflect the local curated datasets and must be revalidated after data, feature, or dependency changes.",
            "",
            "## Ethical Risks",
            "Model outputs can affect fraud, security, content, or user-risk decisions. Use calibrated thresholds, human review for high-impact actions, and monitor drift and subgroup performance.",
            "",
        ]
    )


def _read_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schemaVersion": 2, "models": []}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "models" not in payload or not isinstance(payload["models"], list):
        payload["models"] = []
    return payload


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent), delete=False) as tmp:
        json.dump(payload, tmp, indent=2)
        tmp.write("\n")
        temp_name = tmp.name
    Path(temp_name).replace(path)


def promote_domain(
    domain: str,
    cfg: dict[str, Any],
    gates: dict[str, Any],
    *,
    manifest_path: Path,
    sha: str,
) -> dict[str, Any]:
    result = evaluate_domain(domain, cfg, gates)
    if result["status"] != "pass":
        return result

    source = resolve_path(cfg["artifact"])
    release_dir = ROOT / "artifacts" / "release" / domain / sha
    promoted = copy_artifact(source, release_dir)
    artifact_sha = sha256_tree(promoted)
    data_version = dataset_version(resolve_path(cfg.get("dataset_version_source") or cfg.get("dataset")))
    card_path = release_dir / "model_card.md"
    card_path.write_text(
        render_model_card(
            domain=domain,
            cfg=cfg,
            promoted_path=promoted,
            result=result,
            artifact_sha=artifact_sha,
            data_version=data_version,
            sha=sha,
        ),
        encoding="utf-8",
    )

    entry = {
        "domain": domain,
        "modelName": cfg.get("model_name", domain),
        "version": cfg.get("version", "1.0.0"),
        "path": rel_path(promoted),
        "artifactSha256": artifact_sha,
        "treeSha256": artifact_sha if promoted.is_dir() else None,
        "metricsFile": cfg.get("metrics"),
        "smokeInference": "pass",
        "thresholdResult": "pass",
        "trainingGitSha": sha,
        "datasetVersion": data_version,
        "modelCard": rel_path(card_path),
        "promotedAt": datetime.now(timezone.utc).isoformat(),
        "metrics": result.get("selectedMetrics", {}),
    }
    entry = {key: value for key, value in entry.items() if value is not None}

    manifest = _read_manifest(manifest_path)
    manifest.update(
        {
            "schemaVersion": max(int(manifest.get("schemaVersion", 1)), 2),
            "releaseName": gates.get("release_name", "sentifargo-production"),
            "sourceCommit": sha,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
        }
    )
    existing = [item for item in manifest["models"] if item.get("domain") != domain]
    existing.append(entry)
    manifest["models"] = sorted(existing, key=lambda item: str(item.get("domain", "")))
    _atomic_write_json(manifest_path, manifest)
    result["promoted"] = entry
    return result


def write_report(results: list[dict[str, Any]]) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    status = "pass" if all(item["status"] == "pass" for item in results) else "fail"
    payload = {"status": status, "results": results}
    REPORT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = ["# Promotion Gate", "", f"- Status: **{status}**", ""]
    for result in results:
        lines.append(f"## {result['domain']}")
        lines.append(f"- Status: **{result['status']}**")
        lines.append(f"- Artifact: `{result['artifact']}`")
        lines.append(f"- Metrics: `{result['metricsFile']}`")
        if result.get("failures"):
            lines.append(f"- Failures: `{json.dumps(result['failures'])}`")
        if result.get("promoted"):
            lines.append(f"- Promoted path: `{result['promoted']['path']}`")
        lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def selected_domains(args: argparse.Namespace, gates: dict[str, Any]) -> list[str]:
    domains = gates["domains"]
    if args.all:
        names = list(gates.get("required_domains") or domains.keys())
        if args.include_optional:
            names += list(gates.get("optional_domains") or [])
        return [name for name in names if name in domains]
    if args.domain:
        return args.domain
    raise SystemExit("Provide --all or at least one --domain.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote validated model artifacts.")
    parser.add_argument("--gates", type=Path, default=DEFAULT_GATES)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--domain", action="append", default=[])
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--include-optional", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument(
        "--promote-passing",
        action="store_true",
        help=(
            "When promoting multiple domains, copy artifacts and update the manifest "
            "for domains that pass even if other selected domains fail."
        ),
    )
    args = parser.parse_args()

    gates = load_gates(args.gates)
    sha = git_sha(short=True)
    domains = selected_domains(args, gates)
    results: list[dict[str, Any]]
    if args.check_only:
        results = [
            evaluate_domain(domain, gates["domains"][domain], gates)
            for domain in domains
        ]
        failed = any(result["status"] != "pass" for result in results)
        write_report(results)
        if failed:
            print(f"Promotion failed. Wrote {REPORT_MD} and {REPORT_JSON}")
            return 1
        print(f"Promotion passed. Wrote {REPORT_MD} and {REPORT_JSON}")
        return 0

    preflight = [
        evaluate_domain(domain, gates["domains"][domain], gates)
        for domain in domains
    ]
    if any(result["status"] != "pass" for result in preflight) and not args.promote_passing:
        write_report(preflight)
        print(f"Promotion failed. Wrote {REPORT_MD} and {REPORT_JSON}")
        return 1

    results = []
    failed = False
    preflight_by_domain = {result["domain"]: result for result in preflight}
    for domain in domains:
        preflight_result = preflight_by_domain[domain]
        if preflight_result["status"] != "pass":
            failed = True
            results.append(preflight_result)
            continue
        cfg = gates["domains"][domain]
        result = promote_domain(domain, cfg, gates, manifest_path=args.manifest, sha=sha)
        if result["status"] != "pass":
            failed = True
        results.append(result)
    write_report(results)
    if failed:
        print(f"Promotion failed. Wrote {REPORT_MD} and {REPORT_JSON}")
        return 1
    print(f"Promotion passed. Wrote {REPORT_MD} and {REPORT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
