from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.db.models import ModelVersion
from app.db.session import get_db
from app.mlops.model_cards import write_model_card
from app.services.audit import record_audit

router = APIRouter(prefix="/models", tags=["models"], dependencies=[Depends(require_roles("admin", "analyst"))])


class ModelCreate(BaseModel):
    model_name: str
    version: str = "latest"
    run_id: str | None = None
    metrics: dict = {}
    artifact_path: str = ""
    status: str = "staging"
    dataset: str = "unknown"


@router.get("")
def list_models(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(ModelVersion).order_by(ModelVersion.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "model_name": r.model_name,
            "version": r.version,
            "run_id": r.run_id,
            "metrics": r.metrics,
            "artifact_path": r.artifact_path,
            "status": r.status,
            "card_path": r.card_path,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.post("")
def register_model(payload: ModelCreate, db: Session = Depends(get_db)) -> dict:
    card_path = ""
    try:
        card_path = str(
            write_model_card(
                model_name=payload.model_name,
                version=payload.version,
                dataset=payload.dataset,
                metrics=payload.metrics or {},
                artifact_path=payload.artifact_path,
                status=payload.status,
                run_id=payload.run_id,
            )
        )
    except Exception:
        card_path = ""

    model = ModelVersion(
        model_name=payload.model_name,
        version=payload.version,
        run_id=payload.run_id,
        metrics=payload.metrics or {},
        artifact_path=payload.artifact_path,
        status=payload.status,
        card_path=card_path,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    record_audit(db, action="register_model", target=model.id)
    return {"id": model.id, "card_path": card_path}
