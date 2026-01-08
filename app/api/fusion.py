from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.fusion.engine import predict_fusion

router = APIRouter(prefix="/fusion", tags=["fusion"])


class FusionSignals(BaseModel):
    fraud: float = Field(default=0.0, ge=0.0, le=1.0)
    cyber: float = Field(default=0.0, ge=0.0, le=1.0)
    behavior: float = Field(default=0.0, ge=0.0, le=1.0)
    vision: float = Field(default=0.0, ge=0.0, le=1.0)
    voice: float = Field(default=0.0, ge=0.0, le=1.0)
    threshold: float = Field(default=0.8, ge=0.0, le=1.0)


@router.post("/analyze")
async def analyze_fusion(payload: FusionSignals) -> dict:
    try:
        signals = payload.model_dump(exclude={"threshold"})
        return predict_fusion(signals, threshold=payload.threshold)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Fusion predict failed: {exc}") from exc
