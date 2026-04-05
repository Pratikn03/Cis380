#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ModuleNotFoundError:
    yaml = None

ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = ROOT / "reports"

RE_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
RE_SENTENCE = re.compile(r"[^.!?]+[.!?]")
RE_CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)
RE_OWNER = re.compile(r"^-\s*Owner:\s*(.+)$", re.MULTILINE)
RE_LAST_VERIFIED = re.compile(r"^-\s*Last verified:\s*(.+)$", re.MULTILINE)
READ_RETRY_ATTEMPTS = 3
READ_RETRY_SLEEP_SECONDS = 0.5


@dataclass
class CheckIssue:
    level: str  # error | warning
    code: str
    path: str
    message: str


def _strip_quotes(value: str) -> str:
    return value.strip().strip('"').strip("'")


def _parse_manifest_fallback(raw: str) -> dict[str, Any]:
    data: dict[str, Any] = {"documents": [], "readme_schema": {"required_sections": []}}
    in_documents = False
    in_required_sections = False
    current_doc: dict[str, Any] | None = None

    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        stripped = line.strip()

        if stripped.startswith("documents:"):
            in_documents = True
            in_required_sections = False
            current_doc = None
            continue

        if stripped.startswith("readme_schema:"):
            in_documents = False
            in_required_sections = False
            current_doc = None
            continue

        if stripped.startswith("required_sections:"):
            in_required_sections = True
            in_documents = False
            continue

        if in_required_sections and stripped.startswith("- "):
            data["readme_schema"]["required_sections"].append(_strip_quotes(stripped[2:]))
            continue

        if in_documents and stripped.startswith("- path:"):
            current_doc = {"path": _strip_quotes(stripped.split(":", 1)[1])}
            data["documents"].append(current_doc)
            continue

        if in_documents and current_doc is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = _strip_quotes(value)
            if key in {"review_cadence_days"}:
                try:
                    current_doc[key] = int(value)
                except ValueError:
                    current_doc[key] = value
            elif key in {"requires_schema"}:
                current_doc[key] = value.lower() == "true"
            else:
                current_doc[key] = value

        if stripped.startswith("version:"):
            try:
                data["version"] = int(stripped.split(":", 1)[1].strip())
            except ValueError:
                data["version"] = stripped.split(":", 1)[1].strip()

        if stripped.startswith("last_updated:"):
            data["last_updated"] = _strip_quotes(stripped.split(":", 1)[1])

    return data


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Manifest not found: {path}")
    raw = _read_text(path)
    if yaml is not None:
        payload = yaml.safe_load(raw)
    else:
        payload = _parse_manifest_fallback(raw)
    if not isinstance(payload, dict):
        raise SystemExit(f"Invalid manifest format: {path}")
    payload.setdefault("documents", [])
    payload.setdefault("readme_schema", {}).setdefault("required_sections", [])
    return payload


def _read_text(path: Path) -> str:
    last_error: Exception | None = None
    for attempt in range(READ_RETRY_ATTEMPTS):
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except TimeoutError as exc:
            last_error = exc
        except OSError as exc:
            # macOS filesystem/desktop sync providers can intermittently raise ETIMEDOUT (errno 60).
            if getattr(exc, "errno", None) != 60:
                raise
            last_error = exc
        if attempt < READ_RETRY_ATTEMPTS - 1:
            time.sleep(READ_RETRY_SLEEP_SECONDS)
    assert last_error is not None
    raise last_error


def _find_h2_duplicates(text: str) -> list[str]:
    headings = re.findall(r"^##\s+(.+)$", text, flags=re.MULTILINE)
    seen: dict[str, int] = {}
    duplicates: list[str] = []
    for heading in headings:
        norm = heading.strip().lower()
        seen[norm] = seen.get(norm, 0) + 1
        if seen[norm] == 2:
            duplicates.append(heading.strip())
    return duplicates


def _check_required_sections(text: str, required: list[str]) -> tuple[bool, str]:
    positions: list[int] = []
    for section in required:
        needle = f"## {section}"
        idx = text.find(needle)
        if idx < 0:
            return False, f"missing required section: '{section}'"
        positions.append(idx)

    if positions != sorted(positions):
        return False, "required sections are out of order"
    return True, "ok"


def _extract_internal_links(path: Path, text: str) -> list[tuple[str, Path]]:
    links: list[tuple[str, Path]] = []
    for raw_target in RE_LINK.findall(text):
        target = raw_target.strip()
        if not target:
            continue
        if target.startswith(("http://", "https://", "mailto:", "tel:", "#")):
            continue
        target = target.split("#", 1)[0]
        if not target:
            continue
        if target.startswith("/"):
            resolved = ROOT / target.lstrip("/")
        else:
            resolved = (path.parent / target).resolve()
        links.append((raw_target, resolved))
    return links


def _sentence_word_lengths(text: str) -> list[int]:
    # Ignore fenced code blocks and markdown tables to avoid false readability alerts.
    text = RE_CODE_FENCE.sub(" ", text)
    filtered_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if not stripped:
            continue
        if stripped.startswith(("#", "|", "- ", "* ", ">")):
            continue
        if re.match(r"^\d+\.\s", stripped):
            continue
        filtered_lines.append(line)
    text = "\n".join(filtered_lines)
    lengths: list[int] = []
    for sentence in RE_SENTENCE.findall(text.replace("\n", " ")):
        words = re.findall(r"\b[\w'-]+\b", sentence)
        if words:
            lengths.append(len(words))
    return lengths


def _parse_last_verified(text: str) -> dt.date | None:
    match = RE_LAST_VERIFIED.search(text)
    if not match:
        return None
    raw = match.group(1).strip()
    try:
        return dt.date.fromisoformat(raw)
    except ValueError:
        return None


def _write_scorecard(report: dict[str, Any]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "docs_scorecard.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Docs Scorecard",
        "",
        f"- Date: {report['date']}",
        f"- Mode: {report['mode']}",
        f"- Threshold: {report['threshold']}",
        f"- Score: **{report['score']}**",
        f"- Status: **{report['status']}**",
        "",
        "## Dimension scores",
    ]
    for name, value in report["dimensions"].items():
        lines.append(f"- {name}: {value}")

    lines.append("")
    lines.append("## Issues")
    if not report["issues"]:
        lines.append("- None")
    else:
        for issue in report["issues"]:
            lines.append(
                f"- `{issue['level']}` {issue['code']} in `{issue['path']}`: {issue['message']}"
            )

    (REPORTS_DIR / "DOCS_SCORECARD.md").write_text("\n".join(lines), encoding="utf-8")


def run_checks(mode: str, threshold: int, manifest_path: Path) -> int:
    manifest = _load_manifest(manifest_path)
    docs: list[dict[str, Any]] = manifest.get("documents", [])
    required_sections: list[str] = manifest.get("readme_schema", {}).get("required_sections", [])

    issues: list[CheckIssue] = []

    total_docs = len(docs)
    existing_docs = 0

    schema_docs = 0
    schema_pass = 0

    duplicate_docs = 0

    internal_links = 0
    valid_links = 0

    canonical_docs = 0
    canonical_fresh = 0

    readability_docs = 0
    readability_pass = 0

    today = dt.date.today()

    for doc in docs:
        rel_path = str(doc.get("path", "")).strip()
        if not rel_path:
            issues.append(CheckIssue("error", "MANIFEST_PATH", "docs/docs-manifest.yml", "empty path entry"))
            continue

        path = ROOT / rel_path
        if not path.exists():
            issues.append(CheckIssue("error", "MISSING_FILE", rel_path, "file does not exist"))
            continue

        existing_docs += 1
        text = _read_text(path)

        duplicates = _find_h2_duplicates(text)
        if duplicates:
            duplicate_docs += 1
            issues.append(
                CheckIssue(
                    "error",
                    "DUPLICATE_H2",
                    rel_path,
                    f"duplicate '##' headings: {', '.join(duplicates)}",
                )
            )

        if doc.get("requires_schema"):
            schema_docs += 1
            ok, message = _check_required_sections(text, required_sections)
            if ok:
                schema_pass += 1
            else:
                issues.append(CheckIssue("error", "README_SCHEMA", rel_path, message))

            if "## Ownership and canonical links" in text and "canonical" not in text.lower():
                issues.append(
                    CheckIssue(
                        "error",
                        "CANONICAL_LINK",
                        rel_path,
                        "ownership section present but canonical links not documented",
                    )
                )

        if str(doc.get("status", "")).lower() == "canonical":
            canonical_docs += 1
            owner_ok = RE_OWNER.search(text) is not None
            verified = _parse_last_verified(text)
            fresh_ok = verified is not None and (today - verified).days <= 180
            if owner_ok and fresh_ok:
                canonical_fresh += 1
            else:
                if not owner_ok:
                    issues.append(CheckIssue("error", "OWNER_METADATA", rel_path, "missing '- Owner:' metadata"))
                if verified is None:
                    issues.append(
                        CheckIssue(
                            "error",
                            "LAST_VERIFIED_METADATA",
                            rel_path,
                            "missing or invalid '- Last verified: YYYY-MM-DD' metadata",
                        )
                    )
                elif (today - verified).days > 180:
                    issues.append(
                        CheckIssue(
                            "error",
                            "STALE_METADATA",
                            rel_path,
                            f"last verified is stale ({verified.isoformat()})",
                        )
                    )

        if mode == "full":
            for raw_target, resolved in _extract_internal_links(path, text):
                internal_links += 1
                if resolved.exists():
                    valid_links += 1
                else:
                    issues.append(
                        CheckIssue(
                            "error",
                            "BROKEN_LINK",
                            rel_path,
                            f"broken internal link target: {raw_target}",
                        )
                    )

            lengths = _sentence_word_lengths(text)
            readability_docs += 1
            if not lengths:
                readability_pass += 1
            else:
                avg_len = sum(lengths) / len(lengths)
                max_len = max(lengths)
                if avg_len <= 26 and max_len <= 45:
                    readability_pass += 1
                else:
                    issues.append(
                        CheckIssue(
                            "warning",
                            "READABILITY",
                            rel_path,
                            f"sentence lengths high (avg={avg_len:.1f}, max={max_len})",
                        )
                    )

    completeness = round((existing_docs / total_docs) * 100, 2) if total_docs else 100.0
    schema_score = round((schema_pass / schema_docs) * 100, 2) if schema_docs else 100.0
    duplicate_score = 100.0 if existing_docs == 0 else round(((existing_docs - duplicate_docs) / existing_docs) * 100, 2)
    consistency = round((schema_score * 0.7) + (duplicate_score * 0.3), 2)

    if mode == "full":
        link_integrity = round((valid_links / internal_links) * 100, 2) if internal_links else 100.0
        freshness = round((canonical_fresh / canonical_docs) * 100, 2) if canonical_docs else 100.0
        readability = round((readability_pass / readability_docs) * 100, 2) if readability_docs else 100.0
    else:
        link_integrity = 100.0
        freshness = round((canonical_fresh / canonical_docs) * 100, 2) if canonical_docs else 100.0
        readability = 100.0

    score = round(
        (completeness * 0.25)
        + (consistency * 0.20)
        + (link_integrity * 0.20)
        + (freshness * 0.20)
        + (readability * 0.15),
        2,
    )

    blocking_errors = [i for i in issues if i.level == "error"]
    status = "pass" if (score >= threshold and not blocking_errors) else "fail"

    report = {
        "date": today.isoformat(),
        "mode": mode,
        "threshold": threshold,
        "score": score,
        "status": status,
        "dimensions": {
            "completeness": completeness,
            "consistency": consistency,
            "link_integrity": link_integrity,
            "freshness": freshness,
            "readability": readability,
        },
        "issues": [i.__dict__ for i in issues],
    }

    _write_scorecard(report)
    print(json.dumps(report, indent=2))

    return 0 if status == "pass" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Sentifargo documentation quality checker")
    parser.add_argument("--mode", choices=["fast", "full"], default="full")
    parser.add_argument("--threshold", type=int, default=95)
    parser.add_argument("--manifest", default="docs/docs-manifest.yml")
    args = parser.parse_args()

    return run_checks(args.mode, args.threshold, ROOT / args.manifest)


if __name__ == "__main__":
    raise SystemExit(main())
