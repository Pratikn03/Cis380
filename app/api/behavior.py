from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


class BehaviorRequest(BaseModel):
    features: list[float]


_MODEL_PATH = Path("models") / "behavior" / "behavior_lof.pkl"
_behavior = None
_behavior_error: str | None = None
_scaler = None
_lof = None


def _use_model_backend() -> bool:
    return os.getenv("BEHAVIOR_MODEL_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}


def _heuristic_score(features: list[float]) -> float:
    if not features:
        return 0.0
    values = [float(v) for v in features[:10]]
    mean = sum(values) / max(len(values), 1)
    variance = sum((v - mean) ** 2 for v in values) / max(len(values), 1)
    scaled = (abs(mean) * 0.6) + (variance * 0.4)
    return float(min(max(scaled / 10.0, 0.0), 1.0))


def _load_behavior() -> None:
    global _behavior, _behavior_error, _scaler, _lof

    if _behavior is not None:
        return
    if not _MODEL_PATH.exists():
        return
    if _behavior_error is not None:
        return

    try:
        import joblib

        _behavior = joblib.load(_MODEL_PATH)
    except Exception as exc:  # pragma: no cover - local artifact dependent
        _behavior_error = str(exc)
        return

    if isinstance(_behavior, dict):
        _scaler = _behavior.get("preprocessor")
        _lof = _behavior.get("model")


@router.post("/behavior")
def predict_behavior(req: BehaviorRequest):
    if not _use_model_backend():
        return {
            "score": _heuristic_score(req.features),
            "input_features": len(req.features),
            "expected_features": None,
        }

    _load_behavior()
    if _scaler is None or _lof is None:
        detail = "Behavior model not found."
        if _MODEL_PATH.exists() and _behavior_error:
            detail = f"Behavior model failed to load: {_behavior_error}"
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

    try:
        import numpy as np

        expected = int(getattr(_scaler, "n_features_in_", 0) or 0)
        feats = list(req.features)
        if expected:
            feats = (feats + [0.0] * expected)[:expected]
        X = np.array(feats, dtype=float).reshape(1, -1)
        Xs = _scaler.transform(X)
        score = float(_lof.decision_function(Xs)[0])

        return {
            "score": score,
            "input_features": len(req.features),
            "expected_features": expected or None,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Behavior inference failed: {exc}",
        ) from exc
