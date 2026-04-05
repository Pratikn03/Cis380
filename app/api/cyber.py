from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


class CyberRequest(BaseModel):
    features: list[float]


_MODEL_PATH = Path("models") / "cyber" / "supervised" / "cyber_model.pkl"
_cyber_model = None
_cyber_model_error: str | None = None


def _use_model_backend() -> bool:
    return os.getenv("CYBER_MODEL_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}


def _heuristic_score(features: list[float]) -> float:
    if not features:
        return 0.0
    window = [abs(v) for v in features[:8]]
    magnitude = sum(window) / max(len(window), 1)
    return float(min(max(magnitude / 5.0, 0.0), 1.0))


def _get_cyber_model():
    global _cyber_model, _cyber_model_error

    if _cyber_model is not None:
        return _cyber_model
    if not _MODEL_PATH.exists():
        return None
    if _cyber_model_error is not None:
        return None

    try:
        import joblib

        _cyber_model = joblib.load(_MODEL_PATH)
    except Exception as exc:  # pragma: no cover - local artifact dependent
        _cyber_model_error = str(exc)
        return None
    return _cyber_model


@router.post("/cyber")
def predict_cyber(req: CyberRequest):
    if not _use_model_backend():
        return {
            "score": _heuristic_score(req.features),
            "input_features": len(req.features),
            "expected_features": None,
        }

    cyber_model = _get_cyber_model()
    if cyber_model is None:
        detail = "Cyber model not found."
        if _MODEL_PATH.exists() and _cyber_model_error:
            detail = f"Cyber model failed to load: {_cyber_model_error}"
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

    try:
        import numpy as np

        expected = int(getattr(cyber_model, "n_features_in_", 0) or 0)
        feats = list(req.features)
        if expected:
            feats = (feats + [0.0] * expected)[:expected]
        X = np.array(feats, dtype=float).reshape(1, -1)

        if hasattr(cyber_model, "predict_proba"):
            score = float(cyber_model.predict_proba(X)[0][1])
        elif hasattr(cyber_model, "decision_function"):
            score = float(cyber_model.decision_function(X)[0])
        else:
            score = float(cyber_model.predict(X)[0])

        return {
            "score": score,
            "input_features": len(req.features),
            "expected_features": expected or None,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cyber inference failed: {exc}",
        ) from exc
