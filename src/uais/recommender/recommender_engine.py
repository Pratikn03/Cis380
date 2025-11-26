"""Core scoring and recommendation pipeline for the chatbot."""
from __future__ import annotations

from typing import Dict, Any, List

import numpy as np

from .load_models import load_all_models
from .preprocess import parse_text_to_event
from .utils import align_features_for_model, sigmoid
from .feature_engineering import build_meta_features, META_FEATURE_NAMES
from .explain import explain_recommendation


def _score_binary_model(model, features: Dict[str, Any]) -> float:
    if model is None:
        return 0.0
    X = align_features_for_model(model, features)
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)[0]
        return float(proba[1])
    if hasattr(model, "decision_function"):
        score = float(model.decision_function(X)[0])
        return float(sigmoid(score))
    pred = float(model.predict(X)[0])
    return pred


def _score_anomaly_model(model, features: Dict[str, Any]) -> float:
    if model is None:
        return 0.0
    X = align_features_for_model(model, features)
    if hasattr(model, "decision_function"):
        score = float(model.decision_function(X)[0])
        return float(1.0 - sigmoid(score))
    if hasattr(model, "score_samples"):
        score = float(model.score_samples(X)[0])
        return float(1.0 - sigmoid(score))
    pred = float(model.predict(X)[0])
    return 1.0 if pred < 0 else 0.0


def _fuse_scores(models: Dict[str, Any], scores: Dict[str, float]) -> float:
    fusion_model = models.get("fusion")
    if fusion_model is not None:
        X = np.array([[scores.get("fraud", 0.0), scores.get("cyber", 0.0), scores.get("behavior", 0.0)]])
        if hasattr(fusion_model, "predict_proba"):
            proba = fusion_model.predict_proba(X)[0][1]
            return float(proba)
        if hasattr(fusion_model, "decision_function"):
            score = float(fusion_model.decision_function(X)[0])
            return float(sigmoid(score))
    vals = [scores.get("fraud", 0.0), scores.get("cyber", 0.0), scores.get("behavior", 0.0)]
    return float(np.mean(vals))


def _recommend_action(models: Dict[str, Any], meta_features: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
    rec_model = models.get("recommender")
    features_vec = meta_features.reshape(1, -1)
    if rec_model is not None:
        if hasattr(rec_model, "predict_proba"):
            proba = rec_model.predict_proba(features_vec)[0]
            pred = rec_model.predict(features_vec)[0]
            confidence = float(np.max(proba))
        else:
            pred = rec_model.predict(features_vec)[0]
            confidence = 0.5
        action = str(pred)
        return {
            "action": action,
            "confidence": confidence,
            "rec_model": rec_model,
            "features_vec": features_vec,
            "feature_names": feature_names,
        }

    # Fallback: threshold on fusion
    fusion_idx = feature_names.index("fusion_score")
    fusion_val = float(meta_features[fusion_idx])
    if fusion_val >= 0.85:
        action = "BLOCK"
    elif fusion_val >= 0.7:
        action = "REVIEW"
    elif fusion_val >= 0.5:
        action = "MONITOR"
    else:
        action = "ALLOW"
    return {
        "action": action,
        "confidence": fusion_val if fusion_val >= 0.5 else 1.0 - fusion_val,
        "rec_model": None,
        "features_vec": features_vec,
        "feature_names": feature_names,
    }


def recommend_from_scores(scores: Dict[str, float], event_features: Dict[str, Any] | None = None) -> Dict[str, Any]:
    models = load_all_models()
    event_features = event_features or {}

    # Ensure required keys exist
    scores = {
        "fraud": float(scores.get("fraud", 0.0)),
        "cyber": float(scores.get("cyber", 0.0)),
        "behavior": float(scores.get("behavior", 0.0)),
        "fusion": float(scores.get("fusion", scores.get("fraud", 0.0))),
    }

    meta_features, feature_names = build_meta_features(scores, event_features)
    decision = _recommend_action(models, meta_features, feature_names)
    action = decision["action"]
    confidence = decision["confidence"]

    explanation = explain_recommendation(
        action=action,
        scores=scores,
        event_features=event_features,
        rec_model=decision["rec_model"],
        meta_features=decision["features_vec"],
        meta_feature_names=decision["feature_names"],
    )

    return {
        "action": action,
        "confidence": confidence,
        "scores": scores,
        "meta_features": meta_features.tolist(),
        "meta_feature_names": feature_names,
        "explanation": explanation,
    }


def recommend_from_text(text: str) -> Dict[str, Any]:
    models = load_all_models()
    event_features = parse_text_to_event(text)
    if not event_features:
        raise ValueError("Could not parse any features from your input. Use key=value pairs or JSON-like input.")

    fraud_score = _score_binary_model(models.get("fraud_model"), event_features)
    cyber_score = _score_binary_model(models.get("cyber_model"), event_features)
    behavior_score = _score_anomaly_model(models.get("behavior_lof"), event_features)

    scores = {
        "fraud": fraud_score,
        "cyber": cyber_score,
        "behavior": behavior_score,
    }
    scores["fusion"] = _fuse_scores(models, scores)

    return recommend_from_scores(scores, event_features=event_features)


__all__ = ["recommend_from_text", "recommend_from_scores"]
