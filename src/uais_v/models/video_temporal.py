from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

import joblib
import numpy as np

VIDEO_TEMPORAL_MODEL_PATH = Path("models/vision/video_temporal_model.pkl")

# Binary deepfake detector convention used by the video datasets in this repo.
LABEL_MAP: dict[str, int] = {"real": 0, "fake": 1}

# Stable feature schema for the temporal model. Keep this list in sync with:
# - src/train/train_video_temporal.py
# - api/routes/vision.py (/api/vision/video/predict)
TEMPORAL_FEATURE_NAMES: list[str] = [
    "flip_rate",
    "flip_count",
    "frames_used",
    "fps",
    "max_conf_mean",
    "max_conf_std",
    "prob_l1_mean",
    "prob_l1_std",
    "emb_cos_mean",
    "emb_cos_std",
    "pixel_diff_mean",
    "pixel_diff_std",
    "entropy_mean",
    "entropy_std",
]


def _mean_std(values: Sequence[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return 0.0, 0.0
    mean = float(np.mean(arr))
    std = float(np.std(arr)) if arr.size > 1 else 0.0
    return mean, std


def build_temporal_feature_dict(
    *,
    flip_rate: float,
    flip_count: int,
    frames_used: int,
    fps: float,
    max_confs: Sequence[float],
    l1_diffs: Sequence[float],
    cos_sims: Sequence[float],
    pixel_diffs: Sequence[float],
    entropies: Sequence[float],
) -> dict[str, float]:
    max_conf_mean, max_conf_std = _mean_std(max_confs)
    prob_l1_mean, prob_l1_std = _mean_std(l1_diffs)
    emb_cos_mean, emb_cos_std = _mean_std(cos_sims)
    pixel_diff_mean, pixel_diff_std = _mean_std(pixel_diffs)
    entropy_mean, entropy_std = _mean_std(entropies)

    return {
        "flip_rate": float(flip_rate),
        "flip_count": float(int(flip_count)),
        "frames_used": float(int(frames_used)),
        "fps": float(fps),
        "max_conf_mean": float(max_conf_mean),
        "max_conf_std": float(max_conf_std),
        "prob_l1_mean": float(prob_l1_mean),
        "prob_l1_std": float(prob_l1_std),
        "emb_cos_mean": float(emb_cos_mean),
        "emb_cos_std": float(emb_cos_std),
        "pixel_diff_mean": float(pixel_diff_mean),
        "pixel_diff_std": float(pixel_diff_std),
        "entropy_mean": float(entropy_mean),
        "entropy_std": float(entropy_std),
    }


def vectorize_temporal_features(
    features: Mapping[str, float],
    *,
    feature_names: Sequence[str] | None = None,
) -> np.ndarray:
    names = list(feature_names) if feature_names is not None else TEMPORAL_FEATURE_NAMES
    return np.array([[float(features.get(name, 0.0)) for name in names]], dtype=float)


@lru_cache(maxsize=1)
def load_video_temporal_model(
    *,
    path: Path = VIDEO_TEMPORAL_MODEL_PATH,
) -> dict[str, Any]:
    if not path.exists():
        return {"available": False, "path": str(path), "error": "model not found", "model": None, "scaler": None, "feature_names": None}

    try:
        obj = joblib.load(path)
    except Exception as exc:  # pragma: no cover
        return {"available": False, "path": str(path), "error": str(exc), "model": None, "scaler": None, "feature_names": None}

    model = None
    scaler = None
    feature_names = None
    label_map = LABEL_MAP

    if isinstance(obj, dict):
        model = obj.get("model")
        scaler = obj.get("scaler")
        feature_names = obj.get("feature_names")
        label_map = obj.get("label_map") or LABEL_MAP
    else:
        model = obj

    return {
        "available": model is not None,
        "path": str(path),
        "error": None,
        "model": model,
        "scaler": scaler,
        "feature_names": feature_names,
        "label_map": label_map,
    }


def predict_temporal_confidence(
    features: Mapping[str, float],
) -> tuple[float | None, dict[str, Any]]:
    bundle = load_video_temporal_model()
    if not bundle.get("available") or bundle.get("model") is None:
        return None, {"available": False, "path": bundle.get("path"), "error": bundle.get("error")}

    model = bundle["model"]
    scaler = bundle.get("scaler")
    feature_names = bundle.get("feature_names") or TEMPORAL_FEATURE_NAMES

    X = vectorize_temporal_features(features, feature_names=feature_names)
    if scaler is not None:
        try:
            X = scaler.transform(X)
        except Exception as exc:  # pragma: no cover
            return None, {"available": False, "path": bundle.get("path"), "error": f"scaler transform failed: {exc}"}

    try:
        if hasattr(model, "predict_proba"):
            proba = float(model.predict_proba(X)[0][1])
        elif hasattr(model, "decision_function"):
            raw = float(model.decision_function(X)[0])
            proba = float(1.0 / (1.0 + np.exp(-raw)))
        else:
            proba = float(model.predict(X)[0])
    except Exception as exc:  # pragma: no cover
        return None, {"available": False, "path": bundle.get("path"), "error": f"predict failed: {exc}"}

    proba = float(min(max(proba, 0.0), 1.0))
    return proba, {"available": True, "path": bundle.get("path"), "feature_names": list(feature_names)}


__all__ = [
    "VIDEO_TEMPORAL_MODEL_PATH",
    "LABEL_MAP",
    "TEMPORAL_FEATURE_NAMES",
    "build_temporal_feature_dict",
    "vectorize_temporal_features",
    "load_video_temporal_model",
    "predict_temporal_confidence",
]

