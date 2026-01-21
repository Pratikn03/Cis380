from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.db.models import Job
from app.db.session import get_db
from app.services.audit import record_audit
from app.workers import tasks
from app.workers.celery_app import celery

router = APIRouter(prefix="/jobs", tags=["jobs"], dependencies=[Depends(require_roles("admin"))])

LOG_DIR = Path("logs/jobs")


try:  # Pydantic v2
    from pydantic import ConfigDict  # type: ignore

    class JobStartRequest(BaseModel):
        job_type: str | None = None
        type: str | None = None
        payload: dict[str, Any] = {}

        model_config = ConfigDict(populate_by_name=True)

except Exception:  # Pydantic v1

    class JobStartRequest(BaseModel):
        job_type: str | None = None
        type: str | None = None
        payload: dict[str, Any] = {}

        class Config:
            allow_population_by_field_name = True


TASK_MAP = {
    "rag_index": tasks.rag_index,
    "rag_eval": tasks.rag_eval,
    "train_model": tasks.train_model,
}


@router.post("/start")
def start_job(payload: JobStartRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    job_type = payload.job_type or payload.type
    if not job_type or job_type not in TASK_MAP:
        raise HTTPException(status_code=400, detail="Unknown job type")
    job = Job(
        job_type=job_type,
        status="queued",
        progress=0.0,
        message="queued",
        payload=payload.payload,
        created_at=datetime.utcnow(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    task = TASK_MAP[job_type]
    if job_type == "train_model":
        script = payload.payload.get("script")
        args = payload.payload.get("args", [])
        if not script:
            raise HTTPException(status_code=400, detail="payload.script is required")
        result = task.delay(job.id, script=script, args=args)
    elif job_type == "rag_index":
        result = task.delay(job.id, rebuild=payload.payload.get("rebuild", False))
    else:
        result = task.delay(job.id)

    job.task_id = result.id
    db.commit()

    record_audit(db, action="start_job", target=job.job_type)
    return {"job_id": job.id, "task_id": job.task_id, "status": job.status}


@router.get("")
def list_jobs(limit: int = 50, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.query(Job).order_by(Job.created_at.desc()).limit(limit).all()
    return [
        {
            "job_id": j.id,
            "task_id": j.task_id,
            "type": j.job_type,
            "status": j.status,
            "progress": j.progress,
            "message": j.message,
            "created_at": j.created_at,
        }
        for j in rows
    ]


@router.get("/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.id,
        "task_id": job.task_id,
        "type": job.job_type,
        "status": job.status,
        "progress": job.progress,
        "message": job.message,
        "payload": job.payload,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
    }


@router.post("/{job_id}/cancel")
def cancel_job(job_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.task_id:
        celery.control.revoke(job.task_id, terminate=True)
    job.status = "cancelled"
    job.message = "cancelled"
    db.commit()
    record_audit(db, action="cancel_job", target=job_id)
    return {"job_id": job.id, "status": job.status}


@router.get("/{job_id}/logs")
def get_job_logs(job_id: str) -> dict[str, Any]:
    path = LOG_DIR / f"{job_id}.log"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Job logs not found")
    return {"job_id": job_id, "logs": path.read_text(encoding="utf-8")}
