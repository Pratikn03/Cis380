from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def _dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            total += item.stat().st_size
    return total


def _file_count(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return 1
    return sum(1 for p in path.rglob("*") if p.is_file())


def validate(catalog_path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    datasets = payload.get("datasets", [])
    results = []
    errors = []
    for entry in datasets:
        name = str(entry.get("name", "unknown"))
        raw_path = entry.get("path", "")
        path = Path(raw_path)
        exists = path.exists()
        size_bytes = _dir_size(path)
        file_count = _file_count(path)
        results.append(
            {
                "name": name,
                "domain": entry.get("domain", ""),
                "path": raw_path,
                "exists": exists,
                "file_count": file_count,
                "size_bytes": size_bytes,
                "license": entry.get("license", ""),
            }
        )
        if not exists:
            errors.append(f"{name}: missing path {raw_path}")
    return {
        "status": "ok" if not errors else "warning",
        "dataset_count": len(results),
        "errors": errors,
        "datasets": results,
    }


def write_report(report: dict[str, Any]) -> None:
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "data_catalog_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    lines = [
        "# Data Catalog Report",
        "",
        f"- status: {report['status']}",
        f"- datasets: {report['dataset_count']}",
        "",
        "## Datasets",
    ]
    for ds in report["datasets"]:
        size_mb = round(ds["size_bytes"] / (1024 * 1024), 2)
        lines.append(
            f"- {ds['name']} ({ds['domain']}): exists={ds['exists']} files={ds['file_count']} size={size_mb}MB"
        )
    if report["errors"]:
        lines.append("")
        lines.append("## Missing Paths")
        lines.extend([f"- {err}" for err in report["errors"]])
    (reports_dir / "data_catalog_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default="data/catalogs/datasets.yaml")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    catalog_path = Path(args.catalog)
    if not catalog_path.exists():
        raise SystemExit(f"Catalog not found: {catalog_path}")
    report = validate(catalog_path)
    write_report(report)
    if args.strict and report["status"] != "ok":
        raise SystemExit("Catalog validation failed")
    print(f"[catalog] status={report['status']} datasets={report['dataset_count']}")


if __name__ == "__main__":
    main()
