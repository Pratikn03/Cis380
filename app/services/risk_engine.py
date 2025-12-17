from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

import joblib
import numpy as np

MODEL_PATHS = {
    "cyber": Path("models/cyber/supervised/cyber_model.pkl"),
    "behavior": Path("models/behavior/behavior_lof.pkl"),
    "fraud": Path("models/fraud/supervised/fraud_model.pkl"),
}

_MODELS: Dict[str, Any] | None = None
_FUSION: dict[str, Any] | None = None

# A small, stable set of generic risk features. If the deployed models expect many
# more features, we pad with zeros so inference doesn't crash.
FEATURE_KEYS = [
    "transaction_amount",
    "clicks_per_minute",
    "files_accessed",
    "device_known",
    "login_time",
]


def _load_models() -> Dict[str, Any]:
    global _MODELS
    if _MODELS is not None:
        return _MODELS

    models: Dict[str, Any] = {}
    for name, path in MODEL_PATHS.items():
        if not path.exists():
            models[name] = None
            continue
        try:
            models[name] = joblib.load(path)
        except Exception:
            models[name] = None

    # Behavior artifact is commonly stored as {"preprocessor": ..., "model": ...}
    beh = models.get("behavior")
    if isinstance(beh, dict):
        models["behavior_scaler"] = beh.get("preprocessor")
        models["behavior_model"] = beh.get("model")
    else:
        models["behavior_scaler"] = None
        models["behavior_model"] = None

    _MODELS = models
    return models


def _build_feature_vector(payload: Mapping[str, Any]) -> np.ndarray:
    vector: list[float] = []
    for k in FEATURE_KEYS:
        v = payload.get(k, 0)
        if isinstance(v, bool):
            vector.append(1.0 if v else 0.0)
        else:
            try:
                vector.append(float(v))
            except Exception:
                vector.append(0.0)
    return np.array(vector, dtype=float).reshape(1, -1)


def _score_model(model: Any, features: np.ndarray) -> float:
    if hasattr(model, "predict_proba"):
        return float(model.predict_proba(features)[0][1])
    if hasattr(model, "decision_function"):
        score = float(model.decision_function(features)[0])
        return 1.0 / (1.0 + np.exp(-score))
    return float(model.predict(features)[0])


def _pad_features(features: np.ndarray, expected: int) -> np.ndarray:
    if expected <= 0:
        return features
    cur = int(features.shape[1])
    if cur == expected:
        return features
    if cur > expected:
        return features[:, :expected]
    pad = np.zeros((features.shape[0], expected - cur), dtype=float)
    return np.concatenate([features, pad], axis=1)

def _load_fusion() -> dict[str, Any]:
    global _FUSION
    if _FUSION is not None:
        return _FUSION

    candidates = [
        Path("models/fusion/fusion_meta_model.pkl"),
        Path("experiments/fusion/models/fusion_meta_model.pkl"),
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            obj = joblib.load(path)
        except Exception as exc:  # pragma: no cover
            _FUSION = {"available": False, "path": str(path), "error": str(exc), "model": None, "scaler": None}
            return _FUSION

        if isinstance(obj, dict):
            model = obj.get("model")
            scaler = obj.get("scaler")
        else:
            model = obj
            scaler = None

        _FUSION = {"available": model is not None, "path": str(path), "error": None, "model": model, "scaler": scaler}
        return _FUSION

    _FUSION = {"available": False, "path": None, "error": "fusion model not found", "model": None, "scaler": None}
    return _FUSION


def _fusion_score(*, cyber_risk: float, behavior_risk: float, fraud_risk: float) -> tuple[float, dict[str, Any]]:
    fusion = _load_fusion()
    if not fusion.get("available") or fusion.get("model") is None:
        return 0.0, {"available": False, "path": fusion.get("path"), "error": fusion.get("error")}

    score_dict = {"behavior": float(behavior_risk), "cyber": float(cyber_risk), "fraud": float(fraud_risk)}
    keys = sorted(score_dict)
    X = np.array([[score_dict[k] for k in keys]], dtype=float)
    scaler = fusion.get("scaler")
    if scaler is not None:
        try:
            X = scaler.transform(X)
        except Exception as exc:  # pragma: no cover
            return 0.0, {"available": False, "path": fusion.get("path"), "error": f"scaler transform failed: {exc}"}

    model = fusion.get("model")
    try:
        if hasattr(model, "predict_proba"):
            score = float(model.predict_proba(X)[0][1])
        elif hasattr(model, "decision_function"):
            raw = float(model.decision_function(X)[0])
            score = float(1.0 / (1.0 + np.exp(-raw)))
        else:
            score = float(model.predict(X)[0])
    except Exception as exc:  # pragma: no cover
        return 0.0, {"available": False, "path": fusion.get("path"), "error": f"fusion predict failed: {exc}"}

    score = float(min(max(score, 0.0), 1.0))
    return score, {"available": True, "path": fusion.get("path"), "inputs": score_dict, "feature_order": keys}


def analyze_risk(payload: Mapping[str, Any]) -> Dict[str, Any]:
    models = _load_models()
    base = _build_feature_vector(payload)

    def _score(name: str) -> float:
        model = models.get(name)
        if model is None:
            return 0.0

        # Some sklearn estimators store the number of expected features.
        expected = int(getattr(model, "n_features_in_", 0) or 0)
        feats = _pad_features(base, expected) if expected else base
        try:
            score = _score_model(model, feats)
        except Exception:
            # If the model is strict about feature counts, fall back to a safe zero score.
            return 0.0
        return float(min(max(score, 0.0), 1.0))

    # Behavior (LOF) is often packaged as scaler + model.
    def _score_behavior() -> float:
        scaler = models.get("behavior_scaler")
        lof = models.get("behavior_model")
        if scaler is None or lof is None:
            return _score("behavior")
        expected = int(getattr(scaler, "n_features_in_", 0) or 0)
        feats = _pad_features(base, expected) if expected else base
        try:
            Xs = scaler.transform(feats)
            raw = float(lof.decision_function(Xs)[0])
            score = 1.0 / (1.0 + np.exp(-raw))
        except Exception:
            return 0.0
        return float(min(max(score, 0.0), 1.0))

    cyber_risk = _score("cyber")
    behavior_risk = _score_behavior()
    fraud_risk = _score("fraud")

    fusion_risk, fusion_meta = _fusion_score(cyber_risk=cyber_risk, behavior_risk=behavior_risk, fraud_risk=fraud_risk)

    return {
        "cyber_risk": cyber_risk,
        "behavior_risk": behavior_risk,
        "fraud_risk": fraud_risk,
        "fusion_risk": fusion_risk,
        "fusion_meta": fusion_meta,
    }
