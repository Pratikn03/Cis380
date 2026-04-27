from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
AUDIO_EXTS = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
TABULAR_EXTS = {".csv", ".tsv"}
TARGET_CANDIDATES = (
    "Class",
    "class",
    "isFraud",
    "isfraud",
    "label",
    "target",
    "attack_cat",
    "Revenue",
    "rating",
)
TEMPORAL_CANDIDATES = ("Time", "time", "timestamp", "date", "datetime", "step")


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()


def _safe_float(value: str) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def _pick_column(header: Iterable[str], candidates: Iterable[str]) -> str | None:
    lower = {col.lower(): col for col in header}
    for candidate in candidates:
        if candidate.lower() in lower:
            return lower[candidate.lower()]
    return None


def _csv_dialect(path: Path) -> str:
    return "\t" if path.suffix.lower() == ".tsv" else ","


def _audit_tabular(files: list[Path]) -> dict[str, Any]:
    rows = 0
    columns: list[str] = []
    missing: Counter[str] = Counter()
    class_balance: Counter[str] = Counter()
    target_col: str | None = None
    temporal_col: str | None = None
    temporal_min_num: float | None = None
    temporal_max_num: float | None = None
    temporal_min_raw: str | None = None
    temporal_max_raw: str | None = None
    seen_hashes: set[str] = set()
    duplicates = 0
    unreadable: list[str] = []

    for path in files:
        try:
            with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as handle:
                reader = csv.DictReader(handle, delimiter=_csv_dialect(path))
                if not reader.fieldnames:
                    continue
                if not columns:
                    columns = [str(col) for col in reader.fieldnames]
                    target_col = _pick_column(columns, TARGET_CANDIDATES)
                    temporal_col = _pick_column(columns, TEMPORAL_CANDIDATES)
                for row in reader:
                    rows += 1
                    row_hash = _hash_text(json.dumps(row, sort_keys=True, ensure_ascii=True))
                    if row_hash in seen_hashes:
                        duplicates += 1
                    else:
                        seen_hashes.add(row_hash)
                    for key, value in row.items():
                        if value is None or str(value).strip() == "":
                            missing[str(key)] += 1
                    if target_col and target_col in row:
                        class_balance[str(row.get(target_col, "")).strip() or "<missing>"] += 1
                    if temporal_col and temporal_col in row:
                        raw = str(row.get(temporal_col, "")).strip()
                        if raw:
                            parsed = _safe_float(raw)
                            if parsed is not None:
                                temporal_min_num = (
                                    parsed if temporal_min_num is None else min(temporal_min_num, parsed)
                                )
                                temporal_max_num = (
                                    parsed if temporal_max_num is None else max(temporal_max_num, parsed)
                                )
                            temporal_min_raw = raw if temporal_min_raw is None else min(temporal_min_raw, raw)
                            temporal_max_raw = raw if temporal_max_raw is None else max(temporal_max_raw, raw)
        except Exception as exc:
            unreadable.append(f"{path}: {exc}")

    missing_rates = {
        key: round(value / rows, 6) for key, value in missing.most_common(25) if rows > 0
    }
    temporal_coverage: dict[str, Any] = {"column": temporal_col}
    if temporal_col:
        if temporal_min_num is not None and temporal_max_num is not None:
            temporal_coverage.update({"min": temporal_min_num, "max": temporal_max_num})
        else:
            temporal_coverage.update({"min": temporal_min_raw, "max": temporal_max_raw})

    return {
        "kind": "tabular",
        "files": [str(path) for path in files],
        "row_count": rows,
        "column_count": len(columns),
        "columns": columns[:50],
        "target_column": target_col,
        "class_balance": dict(class_balance),
        "missing_rates": missing_rates,
        "duplicate_rows": duplicates,
        "duplicate_rate": round(duplicates / rows, 6) if rows else 0.0,
        "temporal_coverage": temporal_coverage,
        "unreadable": unreadable,
    }


def _audit_file_tree(domain_dir: Path, files: list[Path]) -> dict[str, Any]:
    by_ext: Counter[str] = Counter(path.suffix.lower() or "<none>" for path in files)
    class_counts: dict[str, int] = {}
    for child in sorted(domain_dir.iterdir()) if domain_dir.exists() else []:
        if child.is_dir():
            class_counts[child.name] = sum(1 for p in child.rglob("*") if p.is_file())

    duplicate_files = 0
    seen_sizes: dict[tuple[int, str], Path] = {}
    for path in files:
        try:
            key = (path.stat().st_size, path.name)
        except OSError:
            continue
        if key in seen_sizes:
            duplicate_files += 1
        else:
            seen_sizes[key] = path

    return {
        "kind": "files",
        "file_count": len(files),
        "by_extension": dict(by_ext),
        "class_balance": class_counts,
        "missing_rates": {},
        "duplicate_files_estimate": duplicate_files,
        "duplicate_rate": round(duplicate_files / len(files), 6) if files else 0.0,
        "temporal_coverage": {},
        "unreadable": [],
    }


def audit_domain(domain_dir: Path) -> dict[str, Any]:
    files = sorted(path for path in domain_dir.rglob("*") if path.is_file())
    tabular = [path for path in files if path.suffix.lower() in TABULAR_EXTS]
    if tabular:
        payload = _audit_tabular(tabular)
    else:
        payload = _audit_file_tree(domain_dir, files)
    payload.update(
        {
            "domain": domain_dir.name,
            "path": str(domain_dir),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    return payload


def render_markdown(audit: dict[str, Any]) -> str:
    balance = audit.get("class_balance") or {}
    balance_line = ", ".join(f"{key}={value}" for key, value in list(balance.items())[:12]) or "n/a"
    missing = audit.get("missing_rates") or {}
    missing_line = ", ".join(f"{key}={value:.2%}" for key, value in list(missing.items())[:8]) or "n/a"
    row_or_file = audit.get("row_count", audit.get("file_count", 0))
    temporal = audit.get("temporal_coverage") or {}
    temporal_line = "n/a"
    if temporal.get("column"):
        temporal_line = f"{temporal.get('column')}: {temporal.get('min')} to {temporal.get('max')}"

    return "\n".join(
        [
            f"# Data Audit: {audit['domain']}",
            "",
            f"- Generated: {audit['generated_at']}",
            f"- Path: `{audit['path']}`",
            f"- Kind: {audit.get('kind', 'unknown')}",
            f"- Rows/files: {row_or_file}",
            f"- Class balance: {balance_line}",
            f"- Missing rates: {missing_line}",
            f"- Duplicates: {audit.get('duplicate_rows', audit.get('duplicate_files_estimate', 0))} ({audit.get('duplicate_rate', 0):.2%})",
            f"- Temporal coverage: {temporal_line}",
            f"- Unreadable/corrupt samples: {len(audit.get('unreadable') or [])}",
            "",
        ]
    )


def write_audit(domain_dir: Path) -> tuple[Path, Path]:
    audit = audit_domain(domain_dir)
    md_path = domain_dir / "data_audit.md"
    json_path = domain_dir / "data_audit.json"
    md_path.write_text(render_markdown(audit), encoding="utf-8")
    json_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    return md_path, json_path


def _domains(root: Path, names: list[str], all_domains: bool) -> list[Path]:
    if all_domains:
        return sorted(path for path in root.iterdir() if path.is_dir())
    return [root / name for name in names]


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate one-screen data audits by domain.")
    parser.add_argument("--root", type=Path, default=Path("data/raw"))
    parser.add_argument("--domain", action="append", default=[])
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if not args.all and not args.domain:
        args.all = True

    failures = 0
    for domain_dir in _domains(args.root, args.domain, args.all):
        if not domain_dir.exists():
            print(f"[audit] missing: {domain_dir}")
            failures += 1
            continue
        md_path, json_path = write_audit(domain_dir)
        print(f"[audit] wrote {md_path} and {json_path}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
