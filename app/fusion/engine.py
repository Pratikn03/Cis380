from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

import os

import joblib
import numpy as np

MODEL_CANDIDATES = [
    Path(os.getenv("FUSION_MODEL_PATH", "models/fusion/fusion_meta_model.pkl")),
    Path("experiments/fusion/models/fusion_meta_model.pkl"),
]
DEFAULT_KEYS = ["behavior", "cyber", "fraud", "vision", "voice"]


def _normalize_keys(keys: Iterable[str]) -> list[str]:
    return [str(k).strip().lower() for k in keys if str(k).strip()]


@lru_cache(maxsize=1)
def _load_model() -> dict[str, Any]:
    model_path = None
    for candidate in MODEL_CANDIDATES:
        if candidate.exists():
            model_path = candidate
            break
    if model_path is None:
        raise FileNotFoundError("Fusion model not found in known locations.")

    obj = joblib.load(model_path)
    if isinstance(obj, dict):
        model = obj.get("model") or obj.get("estimator") or obj.get("clf")
        scaler = obj.get("scaler")
        feature_order = obj.get("feature_order") or obj.get("features")
        keys = _normalize_keys(feature_order or DEFAULT_KEYS)
    else:
        model = obj
        scaler = None
        keys = DEFAULT_KEYS

    if model is None:
        raise RuntimeError("Fusion model loaded without a valid estimator.")

    expected = int(getattr(model, "n_features_in_", 0) or 0)
    if expected and expected <= len(keys):
        keys = keys[:expected]
    elif expected and expected > len(keys):
        # Pad with extra keys if the model expects more inputs.
        keys = keys + [f"feature_{i}" for i in range(len(keys), expected)]

    return {"model": model, "scaler": scaler, "keys": keys, "model_path": str(model_path)}


def _build_vector(signals: dict[str, Any], keys: list[str]) -> np.ndarray:
    values = []
    for key in keys:
        value = signals.get(key, 0.0)
        try:
            values.append(float(value))
        except Exception:
            values.append(0.0)
    return np.array([values], dtype=float)


def predict_fusion(signals: dict[str, Any], threshold: float = 0.8) -> dict[str, Any]:
    payload = _load_model()
    model = payload["model"]
    scaler = payload["scaler"]
    keys: list[str] = payload["keys"]
    model_path = payload.get("model_path")

    X = _build_vector(signals, keys)
    if scaler is not None:
        X = scaler.transform(X)

    if hasattr(model, "predict_proba"):
        score = float(model.predict_proba(X)[0][1])
    elif hasattr(model, "decision_function"):
        raw = float(model.decision_function(X)[0])
        score = 1.0 / (1.0 + np.exp(-raw))
    else:
        score = float(model.predict(X)[0])

    decision = "BLOCK" if score >= threshold else "ALLOW"
    return {
        "fusion_risk": score,
        "decision": decision,
        "threshold": threshold,
        "feature_order": keys,
        "model_path": model_path,
    }
