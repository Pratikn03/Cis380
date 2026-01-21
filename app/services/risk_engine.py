from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping
import os
import time

import joblib
import numpy as np

from app.fusion.engine import predict_fusion

try:
    from app.core.health import MODEL_ERRORS, MODEL_INFERENCE_COUNT, MODEL_INFERENCE_LATENCY
except Exception:  # pragma: no cover - metrics optional
    MODEL_ERRORS = None
    MODEL_INFERENCE_COUNT = None
    MODEL_INFERENCE_LATENCY = None

MODEL_PATHS = {
    "cyber": Path("models/cyber/supervised/cyber_model.pkl"),
    "behavior": Path("models/behavior/behavior_lof.pkl"),
    "fraud": Path("models/fraud/supervised/fraud_model.pkl"),
}

_MODELS: Dict[str, Any] | None = None

# A small, stable set of generic risk features. If the deployed models expect many
# more features, we pad with zeros so inference doesn't crash.
FEATURE_KEYS = [
    "transaction_amount",
    "clicks_per_minute",
    "files_accessed",
    "device_known",
    "login_time",
]

# Demo-only fallback: used when models are noisy or poorly aligned to payloads.
_HEURISTIC_ENABLED = os.getenv("RISK_HEURISTIC_FALLBACK", "true").lower() not in {
    "0",
    "false",
    "no",
}

# Demo-only geo list to make scenarios visibly different. This is not a production signal.
_DEMO_COUNTRY_RISK = {"NG", "BR", "AE"}


def _record_risk_metrics(duration_seconds: float, error: Exception | None = None) -> None:
    if MODEL_INFERENCE_COUNT is None or MODEL_INFERENCE_LATENCY is None:
        return
    model_type = "risk"
    model_name = "risk_engine"
    try:
        if error is not None and MODEL_ERRORS is not None:
            MODEL_ERRORS.labels(model_type, model_name, type(error).__name__).inc()
        MODEL_INFERENCE_COUNT.labels(model_type, model_name).inc()
        MODEL_INFERENCE_LATENCY.labels(model_type, model_name).observe(duration_seconds)
    except Exception:
        pass


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


def _heuristic_risk(payload: Mapping[str, Any]) -> dict[str, float]:
    def _to_float(val: Any, default: float = 0.0) -> float:
        try:
            return float(val)
        except Exception:
            return default

    amount = _to_float(payload.get("transaction_amount"))
    clicks = _to_float(payload.get("clicks_per_minute"))
    files = _to_float(payload.get("files_accessed"))
    login_time = _to_float(payload.get("login_time"))
    device_known = bool(payload.get("device_known", True))
    login_country = str(payload.get("login_country") or "").upper()

    amount_score = min(amount / 10000.0, 1.0)
    clicks_score = min(clicks / 200.0, 1.0)
    files_score = min(files / 200.0, 1.0)
    after_hours = 1.0 if (login_time < 6 or login_time > 22) else 0.0
    device_score = 1.0 if not device_known else 0.0
    country_score = 1.0 if login_country in _DEMO_COUNTRY_RISK else 0.0

    cyber = 0.5 * clicks_score + 0.4 * files_score + 0.1 * after_hours
    behavior = 0.4 * after_hours + 0.4 * device_score + 0.2 * clicks_score
    fraud = 0.6 * amount_score + 0.3 * device_score + 0.1 * country_score

    def clamp(value: float) -> float:
        return float(min(max(value, 0.0), 1.0))
    return {
        "cyber_risk": clamp(cyber),
        "behavior_risk": clamp(behavior),
        "fraud_risk": clamp(fraud),
    }


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


def _fusion_score(
    *, cyber_risk: float, behavior_risk: float, fraud_risk: float
) -> tuple[float, dict[str, Any]]:
    inputs = {
        "behavior": float(behavior_risk),
        "cyber": float(cyber_risk),
        "fraud": float(fraud_risk),
    }
    try:
        result = predict_fusion(inputs)
        return float(result.get("fusion_risk", 0.0)), {
            "available": True,
            "path": result.get("model_path"),
            "decision": result.get("decision"),
            "threshold": result.get("threshold"),
            "feature_order": result.get("feature_order"),
            "inputs": inputs,
        }
    except Exception as exc:
        return 0.0, {"available": False, "path": None, "error": str(exc), "inputs": inputs}


def analyze_risk(payload: Mapping[str, Any]) -> Dict[str, Any]:
    start = time.perf_counter()
    try:
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

        if _HEURISTIC_ENABLED:
            heuristic = _heuristic_risk(payload)
            cyber_risk = max(cyber_risk, heuristic["cyber_risk"])
            behavior_risk = max(behavior_risk, heuristic["behavior_risk"])
            fraud_risk = max(fraud_risk, heuristic["fraud_risk"])

        fusion_risk, fusion_meta = _fusion_score(
            cyber_risk=cyber_risk, behavior_risk=behavior_risk, fraud_risk=fraud_risk
        )

        result = {
            "cyber_risk": cyber_risk,
            "behavior_risk": behavior_risk,
            "fraud_risk": fraud_risk,
            "fusion_risk": fusion_risk,
            "fusion_meta": fusion_meta,
        }
    except Exception as exc:
        _record_risk_metrics(time.perf_counter() - start, error=exc)
        raise
    _record_risk_metrics(time.perf_counter() - start)
    return result
