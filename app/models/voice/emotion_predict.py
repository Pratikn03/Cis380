from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np

from app.models.voice.features import extract_mfcc, extract_audio_signals, load_audio

MODEL_PATH = Path("models/voice_emotion.pkl")
_MODEL = None

SUPPORTED_EMOTIONS: tuple[str, ...] = ("happy", "sad", "angry", "neutral", "fearful")


def _create_fallback_model(*, persist: bool = True):
    from sklearn.linear_model import LogisticRegression

    np.random.seed(42)
    X = np.random.normal(0, 1, (50, 26))
    y = np.array(["happy"] * 10 + ["sad"] * 10 + ["angry"] * 10 + ["neutral"] * 10 + ["fearful"] * 10)
    # liblinear avoids numerical issues seen in some SciPy/NumPy combos while still
    # providing predict_proba + classes_ for the demo UI.
    clf = LogisticRegression(max_iter=200, solver="liblinear").fit(X, y)
    if persist:
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(clf, MODEL_PATH)
    return clf


def _load_model():
    global _MODEL
    if _MODEL is None:
        if MODEL_PATH.exists():
            try:
                _MODEL = joblib.load(MODEL_PATH)
            except Exception:
                # If a local artifact is incompatible with the current runtime (common across
                # numpy/scikit-learn upgrades), fall back to a tiny in-memory model so the demo
                # stays usable. We intentionally do not overwrite the on-disk artifact.
                _MODEL = _create_fallback_model(persist=False)
            else:
                # Guarantee stable class support for downstream UI/API consumers.
                # If a legacy artifact is missing a supported emotion, switch to a
                # best-effort fallback model that includes all `SUPPORTED_EMOTIONS`.
                model_classes = (
                    [str(c) for c in getattr(_MODEL, "classes_", [])]
                    if getattr(_MODEL, "classes_", None) is not None
                    else []
                )
                missing = [emo for emo in SUPPORTED_EMOTIONS if emo not in model_classes] if model_classes else []
                if missing:
                    _MODEL = _create_fallback_model(persist=False)
        else:
            _MODEL = _create_fallback_model(persist=True)
    return _MODEL


def _predict_single(model: Any, feature: np.ndarray) -> tuple[str, float, dict[str, float] | None]:
    if hasattr(model, "predict_proba"):
        probas = model.predict_proba([feature])[0]
        classes = [str(c) for c in getattr(model, "classes_", [])]
        if classes and len(classes) == len(probas):
            vector = {classes[i]: float(probas[i]) for i in range(len(classes))}
            # Ensure stable keys for downstream consumers (even if a legacy model is missing a class).
            for emo in SUPPORTED_EMOTIONS:
                vector.setdefault(emo, 0.0)
        else:
            vector = None
        idx = int(np.argmax(probas))
        label = str(model.classes_[idx]) if hasattr(model, "classes_") else str(idx)
        confidence = float(probas[idx])
        return label, confidence, vector
    label = str(model.predict([feature])[0])
    return label, 0.5, None


def _segment_predictions(audio: np.ndarray, sr: int, model: Any, *, max_segments: int = 5) -> dict[str, Any]:
    """Best-effort per-segment predictions to surface 'emotion shifts' in a clip."""
    duration_sec = float(audio.size / max(1, sr))
    n_segments = min(max_segments, max(1, int(duration_sec)))  # ~1 segment per second, capped
    seg_len = max(1, int(audio.size / n_segments))

    preds: list[dict[str, Any]] = []
    labels: list[str] = []

    for i in range(n_segments):
        start = i * seg_len
        end = audio.size if i == n_segments - 1 else (i + 1) * seg_len
        segment = audio[start:end]
        feat = extract_mfcc(segment, sr)
        label, conf, vector = _predict_single(model, feat)
        labels.append(label)
        preds.append(
            {
                "segment": i,
                "emotion": label,
                "confidence": round(float(conf), 4),
                "emotion_vector": None if vector is None else {k: round(v, 6) for k, v in vector.items()},
            }
        )

    shifts = 0
    for a, b in zip(labels, labels[1:]):
        if a != b:
            shifts += 1

    return {
        "segments": n_segments,
        "emotion_shift_count": shifts,
        "predictions": preds,
    }


def predict_emotion(*, audio_bytes: bytes, filename: str | None = None) -> dict[str, Any]:
    audio, sr = load_audio(audio_bytes)
    feature = extract_mfcc(audio, sr)
    model = _load_model()
    label, confidence, vector = _predict_single(model, feature)
    signals = extract_audio_signals(audio, sr)
    segments = _segment_predictions(audio, sr, model, max_segments=5)
    model_classes = [str(c) for c in getattr(model, "classes_", [])] if getattr(model, "classes_", None) is not None else []
    missing = [emo for emo in SUPPORTED_EMOTIONS if emo not in model_classes] if model_classes else []

    payload: dict[str, Any] = {
        "emotion": label,
        "confidence": round(float(confidence), 4),
        "signals": signals,
        "segments": segments,
        "supported_emotions": list(SUPPORTED_EMOTIONS),
    }
    if model_classes:
        payload["model_emotions"] = model_classes
    if missing:
        payload["missing_emotions"] = missing
    if vector is not None:
        payload["emotion_vector"] = {k: round(float(v), 6) for k, v in vector.items()}
    if filename:
        payload["filename_hint"] = filename
    return payload
