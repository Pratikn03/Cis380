from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from typing import Any

from app.rag.dsa_pipeline import ingest_documents
from app.workers.celery_app import celery
from app.workers.job_log import append_job_log
from app.db.models import Job
from app.db.session import SessionLocal


def _update_job(job_id: str, **fields: Any) -> None:
    with SessionLocal() as db:
        job = db.get(Job, job_id)
        if not job:
            return
        for key, value in fields.items():
            setattr(job, key, value)
        db.commit()


def _run_script(job_id: str, args: list[str]) -> None:
    append_job_log(job_id, f"Running: {' '.join(args)}")
    result = subprocess.run(args, capture_output=True, text=True)
    if result.stdout:
        append_job_log(job_id, result.stdout.strip())
    if result.stderr:
        append_job_log(job_id, result.stderr.strip())
    result.check_returncode()


@celery.task(bind=True)
def rag_index(self, job_id: str, rebuild: bool = False) -> dict:
    _update_job(
        job_id,
        status="running",
        progress=0.1,
        started_at=datetime.utcnow(),
        message="starting",
    )
    append_job_log(job_id, "Starting RAG index build")
    try:
        stats = ingest_documents(rebuild=rebuild)
        append_job_log(job_id, f"Index built: {stats}")
        _update_job(
            job_id,
            status="done",
            progress=1.0,
            message="completed",
            finished_at=datetime.utcnow(),
        )
        return stats
    except Exception as exc:
        append_job_log(job_id, f"Error: {exc}")
        _update_job(
            job_id,
            status="failed",
            progress=1.0,
            message=str(exc),
            finished_at=datetime.utcnow(),
        )
        raise


@celery.task(bind=True)
def rag_eval(self, job_id: str) -> dict:
    _update_job(
        job_id,
        status="running",
        progress=0.1,
        started_at=datetime.utcnow(),
        message="starting",
    )
    append_job_log(job_id, "Evaluating RAG metrics")
    try:
        _run_script(job_id, [sys.executable, "scripts/rag/evaluate_dsa.py"])
        _update_job(
            job_id,
            status="done",
            progress=1.0,
            message="completed",
            finished_at=datetime.utcnow(),
        )
        return {"status": "ok"}
    except Exception as exc:
        append_job_log(job_id, f"Error: {exc}")
        _update_job(
            job_id,
            status="failed",
            progress=1.0,
            message=str(exc),
            finished_at=datetime.utcnow(),
        )
        raise


@celery.task(bind=True)
def train_model(self, job_id: str, script: str, args: list[str] | None = None) -> dict:
    _update_job(
        job_id,
        status="running",
        progress=0.1,
        started_at=datetime.utcnow(),
        message="starting",
    )
    append_job_log(job_id, f"Training via {script}")
    try:
        cmd = [sys.executable, script] + (args or [])
        _run_script(job_id, cmd)
        _update_job(
            job_id,
            status="done",
            progress=1.0,
            message="completed",
            finished_at=datetime.utcnow(),
        )
        return {"status": "ok"}
    except Exception as exc:
        append_job_log(job_id, f"Error: {exc}")
        _update_job(
            job_id,
            status="failed",
            progress=1.0,
            message=str(exc),
            finished_at=datetime.utcnow(),
        )
        raise
