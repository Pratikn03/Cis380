from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.db.models import Run
from app.db.session import get_db
from app.services.audit import record_audit

router = APIRouter(prefix="/models", tags=["models"], dependencies=[Depends(require_roles("admin", "analyst"))])


class ModelCreate(BaseModel):
    run_type: str = "model"
    metrics: dict = {}
    artifacts: dict = {}


@router.get("")
def list_models(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(Run).order_by(Run.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "run_type": r.run_type,
            "metrics": r.metrics,
            "artifacts": r.artifacts,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.post("")
def register_model(payload: ModelCreate, db: Session = Depends(get_db)) -> dict:
    run = Run(run_type=payload.run_type, metrics=payload.metrics, artifacts=payload.artifacts)
    db.add(run)
    db.commit()
    db.refresh(run)
    record_audit(db, action="register_model", target=run.id)
    return {"id": run.id}
