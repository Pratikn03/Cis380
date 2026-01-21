from __future__ import annotations

from pathlib import Path
from datetime import datetime

LOG_DIR = Path("logs/jobs")


def append_job_log(job_id: str, message: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = f"{datetime.utcnow().isoformat()}Z {message}\n"
    (LOG_DIR / f"{job_id}.log").open("a", encoding="utf-8").write(line)
