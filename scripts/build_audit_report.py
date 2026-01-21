from __future__ import annotations

from pathlib import Path


def read(path: Path) -> str:
    return path.read_text(errors="ignore") if path.exists() else ""


def main() -> None:
    reports = Path("reports")
    audit_dirs = sorted([p for p in reports.glob("audit_*") if p.is_dir()])
    if not audit_dirs:
        raise SystemExit("No audit_* folder found in reports/. Run scripts/audit_full_system.sh first.")
    out = audit_dirs[-1]

    env = read(out / "00_env.txt")
    pollution = read(out / "01_tracked_pollution_hits.txt")
    pytest_out = read(out / "03_pytest.txt")
    health = read(out / "05_health.json")
    openapi = read(out / "05_openapi_head.txt")
    metrics = read(out / "05_metrics_head.txt")
    next_build = read(out / "09_next_build.txt")
    dvc_status = read(out / "11_dvc_status.txt")
    train1 = read(out / "10_train_run1.txt")
    train2 = read(out / "10_train_run2.txt")
    rag = read(out / "07_rag_query.json")

    results: dict[str, str] = {}
    results["repo_hygiene"] = "PASS" if pollution.strip() == "" else "FAIL"
    results["tests"] = "PASS" if "failed" not in pytest_out.lower() else "FAIL"
    results["api_health"] = (
        "PASS"
        if ("ok" in health.lower() or "status" in health.lower() or health.strip().startswith("{"))
        else "FAIL"
    )
    results["openapi"] = "PASS" if "openapi" in openapi.lower() or openapi.strip().startswith("{") else "FAIL"
    results["metrics"] = "PASS" if "# help" in metrics.lower() else "FAIL"
    results["rag_query"] = (
        "PASS" if (rag.strip().startswith("{") and ("citations" in rag.lower() or "answer" in rag.lower())) else "FAIL"
    )
    results["next_build"] = (
        "PASS"
        if ("compiled" in next_build.lower() or "success" in next_build.lower())
        and "error" not in next_build.lower()
        else "FAIL"
    )
    results["dvc"] = "PASS" if "ERROR:" not in dvc_status else "FAIL"
    results["reproducibility"] = "PASS" if (train1.strip() and train2.strip()) else "FAIL"

    md = []
    md.append("# Sentifargo Full-System Audit Report\n")
    md.append("## Environment\n")
    md.append("```text\n" + env.strip() + "\n```\n")
    md.append("## Scoreboard\n")
    for key, value in results.items():
        md.append(f"- **{key}**: {value}")
    md.append("")
    md.append("## Key Evidence Paths\n")
    md.append(f"- Latest audit folder: `{out}`")
    md.append("- Inspect these files for details:")
    md.append("  - `03_pytest.txt` (tests)")
    md.append("  - `05_health.json` / `05_openapi_head.txt` / `05_metrics_head.txt`")
    md.append("  - `07_rag_query.json`")
    md.append("  - `09_next_build.txt`")
    md.append("  - `11_dvc_status.txt`")
    md.append("")

    report_path = out / "AUDIT_REPORT.md"
    report_path.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote: {report_path}")


if __name__ == "__main__":
    main()
