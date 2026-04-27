#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.promote_model import (
    DEFAULT_GATES,
    DEFAULT_MANIFEST,
    ROOT,
    evaluate_domain,
    load_gates,
    resolve_path,
    sha256_tree,
)

DEFAULT_REPORT_JSON = ROOT / "reports" / "MODEL_QUALITY_GATE.json"
DEFAULT_REPORT_MD = ROOT / "reports" / "MODEL_QUALITY_GATE.md"


def _thresholds_from_gates(path: Path = DEFAULT_GATES) -> dict[str, list[dict[str, Any]]]:
    try:
        gates = load_gates(path)
    except Exception:
        return {}
    return {
        domain: list((cfg or {}).get("gates", []) or [])
        for domain, cfg in gates.get("domains", {}).items()
    }


THRESHOLDS = _thresholds_from_gates()


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"models": []}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload.get("models"), list):
        payload["models"] = []
    return payload


def _manifest_by_domain(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(entry.get("domain")): entry
        for entry in payload.get("models", [])
        if isinstance(entry, dict) and entry.get("domain")
    }


def _manifest_result(domain: str, entry: dict[str, Any] | None, *, verify_sha: bool) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    if entry is None:
        return {
            "domain": domain,
            "qualityStatus": "fail",
            "metricFailures": [{"metric": "manifest_entry", "passed": False}],
        }

    threshold = str(entry.get("thresholdResult", "")).lower()
    smoke = str(entry.get("smokeInference", "")).lower()
    if threshold not in {"pass", "passed"}:
        failures.append({"metric": "thresholdResult", "actual": threshold, "passed": False})
    if smoke not in {"pass", "passed"}:
        failures.append({"metric": "smokeInference", "actual": smoke, "passed": False})

    artifact_path = resolve_path(str(entry.get("path", "")))
    if not artifact_path.exists():
        failures.append(
            {"metric": "artifact_exists", "path": str(entry.get("path", "")), "passed": False}
        )
    elif verify_sha:
        expected = str(entry.get("treeSha256") or entry.get("artifactSha256") or "").strip()
        actual = sha256_tree(artifact_path)
        if expected and expected != actual:
            failures.append({"metric": "artifactSha256", "passed": False})

    return {
        "domain": domain,
        "modelName": entry.get("modelName"),
        "artifact": entry.get("path"),
        "metricsFile": entry.get("metricsFile"),
        "qualityStatus": "pass" if not failures else "fail",
        "metricFailures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate production model quality gates.")
    parser.add_argument("--gates", default=str(DEFAULT_GATES))
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--report-json", default=str(DEFAULT_REPORT_JSON))
    parser.add_argument("--report-md", default=str(DEFAULT_REPORT_MD))
    parser.add_argument("--skip-sha", action="store_true")
    args = parser.parse_args()

    gates = load_gates(Path(args.gates))
    manifest_path = Path(args.manifest)
    manifest = _load_manifest(manifest_path)
    entries = _manifest_by_domain(manifest)
    required = list(gates.get("required_domains") or gates["domains"].keys())

    gate_results = [
        evaluate_domain(domain, gates["domains"][domain], gates)
        for domain in required
        if domain in gates["domains"]
    ]
    manifest_results = [
        _manifest_result(domain, entries.get(domain), verify_sha=not args.skip_sha)
        for domain in required
    ]

    missing_domains = sorted(set(required) - set(entries))
    failed_gate_domains = sorted(result["domain"] for result in gate_results if result["status"] != "pass")
    failed_manifest_domains = sorted(
        result["domain"] for result in manifest_results if result["qualityStatus"] != "pass"
    )
    status = (
        "pass"
        if not missing_domains and not failed_gate_domains and not failed_manifest_domains
        else "fail"
    )

    report = {
        "status": status,
        "manifest": str(manifest_path),
        "gates": str(args.gates),
        "missingDomains": missing_domains,
        "failedGateDomains": failed_gate_domains,
        "failedManifestDomains": failed_manifest_domains,
        "results": manifest_results,
        "gateResults": gate_results,
        "manifestResults": manifest_results,
    }

    report_json = Path(args.report_json)
    report_md = Path(args.report_md)
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = ["# Model Quality Gate", "", f"- Status: **{status}**", ""]
    if missing_domains:
        lines.append(f"- Missing domains: {', '.join(missing_domains)}")
    if failed_gate_domains:
        lines.append(f"- Failed metric gates: {', '.join(failed_gate_domains)}")
    if failed_manifest_domains:
        lines.append(f"- Failed manifest checks: {', '.join(failed_manifest_domains)}")
    lines.append("")
    for result in gate_results:
        lines.append(f"## {result['domain']}")
        lines.append(f"- Gate status: **{result['status']}**")
        lines.append(f"- Artifact: `{result['artifact']}`")
        lines.append(f"- Metrics: `{result['metricsFile']}`")
        if result["failures"]:
            lines.append(f"- Failures: `{json.dumps(result['failures'])}`")
        manifest_result = next(
            (item for item in manifest_results if item["domain"] == result["domain"]),
            None,
        )
        if manifest_result and manifest_result["qualityStatus"] != "pass":
            lines.append(
                "- Manifest failures: "
                f"`{json.dumps(manifest_result.get('metricFailures', []))}`"
            )
        lines.append("")
    report_md.write_text("\n".join(lines), encoding="utf-8")

    if status != "pass":
        print(f"Model quality gate failed. Wrote {report_md} and {report_json}")
        return 1
    print(f"Model quality gate passed. Wrote {report_md} and {report_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
