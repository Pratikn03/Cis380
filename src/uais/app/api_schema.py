"""Pydantic schemas for the UAIS local inference API."""
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    domain: str = Field(..., description="fraud | cyber | behavior")
    samples: List[Dict[str, Any]]


class PredictResponse(BaseModel):
    domain: str
    predictions: List[float]


__all__ = ["PredictRequest", "PredictResponse"]
