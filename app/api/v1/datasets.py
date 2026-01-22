from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.db.models import Dataset
from app.db.session import get_db
from app.services.audit import record_audit

router = APIRouter(
    prefix="/datasets", tags=["datasets"], dependencies=[Depends(require_roles("admin", "analyst"))]
)


class DatasetCreate(BaseModel):
    name: str
    location: str
    size_bytes: int = 0
    license: str = "unknown"
    description: str = ""


@router.get("")
def list_datasets(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(Dataset).order_by(Dataset.created_at.desc()).all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "location": d.location,
            "size_bytes": d.size_bytes,
            "license": d.license,
            "description": d.description,
            "created_at": d.created_at,
        }
        for d in rows
    ]


@router.post("")
def create_dataset(payload: DatasetCreate, db: Session = Depends(get_db)) -> dict:
    if db.query(Dataset).filter(Dataset.name == payload.name).first():
        raise HTTPException(status_code=400, detail="Dataset already exists")
    ds = Dataset(
        name=payload.name,
        location=payload.location,
        size_bytes=payload.size_bytes,
        license=payload.license,
        description=payload.description,
    )
    db.add(ds)
    db.commit()
    db.refresh(ds)
    record_audit(db, action="create_dataset", target=ds.name)
    return {"id": ds.id, "name": ds.name}
