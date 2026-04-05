#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
OUT_MD = REPORTS / "REPRODUCIBILITY_CHECK.md"
OUT_JSON = REPORTS / "REPRODUCIBILITY_CHECK.json"


@dataclass
class Check:
    name: str
    status: str
    details: str


def _run(cmd: list[str], *, timeout: int = 20) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:
        return 1, str(exc)
    text = (proc.stdout or proc.stderr).strip()
    return proc.returncode, text[:400]


def _exists_check(path: str, *, kind: str = "file") -> Check:
    p = ROOT / path
    if kind == "dir":
        ok = p.is_dir()
    else:
        ok = p.is_file()
    return Check(
        name=f"exists:{path}",
        status="ok" if ok else "missing",
        details="present" if ok else "not found",
    )


def _report_freshness(path: str, *, warn_after_hours: int) -> Check:
    p = ROOT / path
    if not p.exists():
        return Check(name=f"freshness:{path}", status="missing", details="report missing")
    if p.stat().st_size == 0:
        return Check(name=f"freshness:{path}", status="missing", details="report is empty")
    age_h = (datetime.now(timezone.utc) - datetime.fromtimestamp(p.stat().st_mtime, timezone.utc)).total_seconds() / 3600.0
    if age_h <= warn_after_hours:
        return Check(
            name=f"freshness:{path}",
            status="ok",
            details=f"age={age_h:.1f}h threshold={warn_after_hours}h",
        )
    return Check(
        name=f"freshness:{path}",
        status="warn",
        details=f"age={age_h:.1f}h threshold={warn_after_hours}h",
    )


def _tool_check(name: str, cmd: list[str]) -> Check:
    code, out = _run(cmd)
    return Check(
        name=f"tool:{name}",
        status="ok" if code == 0 else "missing",
        details=out or f"exit={code}",
    )


def _module_check(module_name: str) -> Check:
    available = importlib.util.find_spec(module_name) is not None
    return Check(
        name=f"module:{module_name}",
        status="ok" if available else "missing",
        details="import spec found" if available else "module unavailable",
    )


def _score(checks: list[Check]) -> float:
    if not checks:
        return 0.0
    total = 0.0
    for check in checks:
        if check.status == "ok":
            total += 1.0
        elif check.status == "warn":
            total += 0.5
    return round((total / len(checks)) * 100.0, 1)


def _status_from_score(score: float) -> str:
    if score >= 90.0:
        return "green"
    if score >= 75.0:
        return "yellow"
    return "red"


def _render_markdown(
    *,
    generated_at: str,
    score: float,
    grade: str,
    checks: list[Check],
) -> str:
    lines = [
        "# Reproducibility Check",
        "",
        f"- Generated: {generated_at}",
        f"- Score: **{score}/100**",
        f"- Grade: **{grade}**",
        "",
        "## Environment",
        f"- Python: `{sys.version.split()[0]}`",
        f"- Platform: `{platform.platform()}`",
        "",
        "## Checks",
        "",
        "| Check | Status | Details |",
        "|---|---|---|",
    ]
    for check in checks:
        lines.append(f"| `{check.name}` | **{check.status}** | {check.details} |")
    return "\n".join(lines)


def main() -> int:
    checks: list[Check] = []

    checks.extend(
        [
            _exists_check("README.md"),
            _exists_check("Makefile"),
            _exists_check("docs/REPRODUCIBILITY.md"),
            _exists_check("scripts/ci_scorecard.sh"),
            _exists_check("scripts/ci_e2e.sh"),
            _exists_check("scripts/system_scorecard.py"),
            _exists_check("app/main.py"),
            _exists_check("tests/e2e", kind="dir"),
            _exists_check("data", kind="dir"),
            _exists_check("models", kind="dir"),
        ]
    )

    checks.extend(
        [
            _tool_check("git", ["git", "--version"]),
            _tool_check("python", [sys.executable, "--version"]),
            _module_check("pytest"),
            _module_check("uvicorn"),
        ]
    )

    checks.extend(
        [
            _report_freshness("reports/TRAINING_DATA.json", warn_after_hours=72),
            _report_freshness("reports/TRAINING_GAPS.json", warn_after_hours=72),
            _report_freshness("reports/PROJECT_AUDIT.json", warn_after_hours=168),
            _report_freshness("reports/SYSTEM_SCORECARD.json", warn_after_hours=72),
            _report_freshness("reports/openapi.json", warn_after_hours=72),
            _report_freshness("reports/CLAIM_EVIDENCE.md", warn_after_hours=168),
            _report_freshness("reports/CONTRACT_DIFF.md", warn_after_hours=168),
        ]
    )

    score = _score(checks)
    grade = _status_from_score(score)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    payload = {
        "generated_at": generated_at,
        "score": score,
        "grade": grade,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "checks": [asdict(check) for check in checks],
    }

    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    OUT_MD.write_text(
        _render_markdown(generated_at=generated_at, score=score, grade=grade, checks=checks),
        encoding="utf-8",
    )
    print(f"wrote {OUT_MD}")
    print(f"wrote {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
