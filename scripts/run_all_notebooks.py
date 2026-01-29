#!/usr/bin/env python3
"""Execute all notebooks sequentially and log failures."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS_DIR = REPO_ROOT / "notebooks"


def _discover_notebooks(root: Path) -> list[Path]:
    notebooks: list[Path] = []
    for path in root.rglob("*.ipynb"):
        if "_executed" in path.parts:
            continue
        if ".ipynb_checkpoints" in path.parts:
            continue
        notebooks.append(path)
    return sorted(notebooks)


def _run_notebook(
    path: Path,
    *,
    output_root: Path,
    log_handle,
    kernel: str | None,
) -> tuple[bool, float, int]:
    rel = path.relative_to(NOTEBOOKS_DIR)
    out_dir = output_root / rel.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "jupyter",
        "nbconvert",
        "--to",
        "notebook",
        "--execute",
        "--ExecutePreprocessor.timeout=-1",
        "--output-dir",
        str(out_dir),
        "--output",
        rel.stem,
        str(path),
    ]
    if kernel:
        cmd += ["--ExecutePreprocessor.kernel_name", kernel]

    log_handle.write(f"\n=== Running {rel} ===\n")
    log_handle.write("Command: " + " ".join(cmd) + "\n")
    log_handle.flush()

    start = time.time()
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), stdout=log_handle, stderr=log_handle)
    elapsed = time.time() - start
    status = "ok" if proc.returncode == 0 else f"failed (exit {proc.returncode})"
    log_handle.write(f"Status: {status} | seconds: {elapsed:.2f}\n")
    log_handle.flush()
    return proc.returncode == 0, elapsed, proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run all notebooks sequentially and log failures."
    )
    parser.add_argument(
        "--output-dir",
        default=str(NOTEBOOKS_DIR / "_executed"),
        help="Directory to write executed notebooks.",
    )
    parser.add_argument(
        "--log",
        default=str(REPO_ROOT / "logs" / "notebook_runner.log"),
        help="Log file path for notebook execution output.",
    )
    parser.add_argument(
        "--summary",
        default=str(REPO_ROOT / "reports" / "notebook_runner_summary.json"),
        help="Summary JSON file path.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip notebooks already marked OK in the existing summary file.",
    )
    parser.add_argument(
        "--start-at",
        default="",
        help="Start execution from the first notebook that matches this relative path.",
    )
    parser.add_argument(
        "--kernel",
        default="",
        help="Optional Jupyter kernel name (default uses notebook metadata).",
    )
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop execution on the first failure.",
    )
    parser.add_argument(
        "--max-notebooks",
        type=int,
        default=0,
        help="Limit number of notebooks to run (0 = all).",
    )
    args = parser.parse_args()

    notebooks = _discover_notebooks(NOTEBOOKS_DIR)
    if not notebooks:
        raise SystemExit(f"No notebooks found under {NOTEBOOKS_DIR}")

    if args.max_notebooks > 0:
        notebooks = notebooks[: int(args.max_notebooks)]

    output_dir = Path(args.output_dir).resolve()
    log_path = Path(args.log).resolve()
    summary_path = Path(args.summary).resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    kernel = args.kernel.strip() or None
    start_at = args.start_at.strip()

    resume_ok: dict[str, dict[str, object]] = {}
    if args.resume and summary_path.exists():
        try:
            prev = json.loads(summary_path.read_text(encoding="utf-8"))
            for entry in prev.get("results", []):
                if entry.get("status") == "ok":
                    resume_ok[str(entry.get("notebook"))] = entry
        except Exception:
            resume_ok = {}

    results: list[dict[str, object]] = []
    failures: list[str] = []
    start_time = datetime.now(timezone.utc)

    print(f"Found {len(notebooks)} notebook(s). Logging to {log_path}")
    with log_path.open("a", encoding="utf-8") as log_handle:
        log_handle.write(
            f"\n\n=== Notebook run started {start_time.isoformat()} ===\n"
        )
        if start_at:
            log_handle.write(f"[runner] start-at: {start_at}\n")
        if resume_ok:
            log_handle.write(
                f"[runner] resume enabled, skipping {len(resume_ok)} notebook(s) already OK\n"
            )
        for idx, nb_path in enumerate(notebooks, start=1):
            rel = nb_path.relative_to(NOTEBOOKS_DIR)
            rel_str = str(rel)
            if start_at and rel_str != start_at:
                continue
            start_at = ""
            if rel_str in resume_ok:
                results.append(resume_ok[rel_str])
                print(f"[{idx}/{len(notebooks)}] {rel} -> skipped (already ok)")
                log_handle.write(f"=== Skipping {rel} (already ok) ===\n")
                continue
            print(f"[{idx}/{len(notebooks)}] {rel}")
            ok, seconds, code = _run_notebook(
                nb_path, output_root=output_dir, log_handle=log_handle, kernel=kernel
            )
            result = {
                "notebook": rel_str,
                "status": "ok" if ok else "failed",
                "seconds": round(seconds, 2),
                "returncode": code,
            }
            results.append(result)
            if not ok:
                failures.append(str(rel))
                print(f"  -> failed (exit {code})")
                if args.stop_on_error:
                    break
            else:
                print("  -> ok")

    end_time = datetime.now(timezone.utc)
    summary = {
        "started_at": start_time.isoformat(),
        "finished_at": end_time.isoformat(),
        "total": len(results),
        "success": sum(1 for r in results if r["status"] == "ok"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
        "failures": failures,
        "output_dir": str(output_dir),
        "log_path": str(log_path),
        "results": results,
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(
        f"Done. Success: {summary['success']}, Failed: {summary['failed']}. "
        f"Summary: {summary_path}"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
