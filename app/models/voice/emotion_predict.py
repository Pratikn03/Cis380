from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Sequence

import joblib
import numpy as np

from app.models.voice.features import (
    extract_mfcc,
    extract_audio_signals,
    load_audio,
    compute_zero_crossing_rate,
    compute_rms,
    compute_pitch,
    compute_spectral_contrast,
)

MODEL_PATH = Path("models/voice_emotion.pkl")
_MODEL = None

SUPPORTED_EMOTIONS: tuple[str, ...] = ("happy", "sad", "angry", "neutral", "fearful")
# Enhanced feature count: 26 MFCC + 5 additional features
FEATURE_COUNT = 31


def _coerce_label_list(values: Iterable[object]) -> list[str]:
    return [str(v) for v in values]


def _decode_classes(
    classes: Sequence[object] | None,
    *,
    label_encoder: Any | None = None,
) -> list[str]:
    if classes is None:
        return []
    try:
        if len(classes) == 0:  # type: ignore[arg-type]
            return []
    except Exception:
        return []
    if label_encoder is not None and hasattr(label_encoder, "inverse_transform"):
        try:
            decoded = label_encoder.inverse_transform(list(classes))
            return _coerce_label_list(decoded)
        except Exception:
            pass
    return _coerce_label_list(classes)


def _get_model_classes(model: Any) -> list[str]:
    """Return model class labels as strings (supports legacy dict artifacts)."""
    if isinstance(model, dict):
        inner = model.get("model")
        label_encoder = model.get("label_encoder")
        return _decode_classes(getattr(inner, "classes_", None), label_encoder=label_encoder)
    return _decode_classes(getattr(model, "classes_", None))


def _transform_features(model: Any, feature: np.ndarray) -> np.ndarray:
    """Apply legacy scaler transforms if present."""
    if isinstance(model, dict):
        scaler = model.get("scaler")
        if scaler is not None and hasattr(scaler, "transform"):
            try:
                return np.asarray(scaler.transform([feature])[0], dtype=np.float64)
            except Exception:
                return feature
    return feature


def _expected_feature_count(model: Any) -> int | None:
    """Return the model's expected feature count if discoverable."""
    candidates: list[Any] = []
    if isinstance(model, dict):
        candidates.extend([model.get("model"), model.get("scaler")])
    else:
        candidates.append(model)

    for obj in candidates:
        n = getattr(obj, "n_features_in_", None)
        if isinstance(n, (int, np.integer)) and int(n) > 0:
            return int(n)
    return None


def _extract_enhanced_features(audio: np.ndarray, sr: int) -> np.ndarray:
    """Extract MFCC + additional audio features for better emotion recognition."""
    # MFCC features (26 values)
    mfcc_feat = extract_mfcc(audio, sr)
    
    # Additional features
    zcr = compute_zero_crossing_rate(audio)
    rms_mean, rms_std = compute_rms(audio)
    pitch_mean, _ = compute_pitch(audio, sr)
    spectral = compute_spectral_contrast(audio, sr)
    
    # Convert None to 0.0
    extra_features = np.array([
        zcr,
        rms_mean,
        rms_std,
        pitch_mean if pitch_mean is not None else 0.0,
        spectral if spectral is not None else 0.0
    ], dtype=np.float64)
    
    return np.concatenate([mfcc_feat, extra_features])


def _create_fallback_model(*, persist: bool = True):
    from sklearn.linear_model import LogisticRegression

    np.random.seed(42)
    X = np.random.normal(0, 1, (50, FEATURE_COUNT))
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
                model_classes = _get_model_classes(_MODEL)
                missing = [emo for emo in SUPPORTED_EMOTIONS if emo not in model_classes] if model_classes else []
                expected = _expected_feature_count(_MODEL)
                if expected is not None and expected != FEATURE_COUNT:
                    _MODEL = _create_fallback_model(persist=False)
                elif missing:
                    _MODEL = _create_fallback_model(persist=False)
        else:
            _MODEL = _create_fallback_model(persist=True)
    return _MODEL


def _predict_single(model: Any, feature: np.ndarray) -> tuple[str, float, dict[str, float] | None]:
    transformed = _transform_features(model, feature)

    if isinstance(model, dict):
        inner = model.get("model")
        if inner is None:
            return "neutral", 0.0, None
        label_encoder = model.get("label_encoder")
        if hasattr(inner, "predict_proba"):
            probas = inner.predict_proba([transformed])[0]
            classes = _decode_classes(getattr(inner, "classes_", None), label_encoder=label_encoder)
            vector = {classes[i]: float(probas[i]) for i in range(min(len(classes), len(probas)))} if classes else None
            if vector is not None:
                for emo in SUPPORTED_EMOTIONS:
                    vector.setdefault(emo, 0.0)
            idx = int(np.argmax(probas))
            label = classes[idx] if classes and idx < len(classes) else str(idx)
            confidence = float(probas[idx])
            return label, confidence, vector

        pred = inner.predict([transformed])[0]
        label = str(pred)
        if label_encoder is not None and hasattr(label_encoder, "inverse_transform"):
            try:
                label = str(label_encoder.inverse_transform([pred])[0])
            except Exception:
                pass
        return label, 0.5, None

    if hasattr(model, "predict_proba"):
        probas = model.predict_proba([transformed])[0]
        classes = _decode_classes(getattr(model, "classes_", None))
        if classes and len(classes) == len(probas):
            vector = {classes[i]: float(probas[i]) for i in range(len(classes))}
            for emo in SUPPORTED_EMOTIONS:
                vector.setdefault(emo, 0.0)
        else:
            vector = None
        idx = int(np.argmax(probas))
        label = classes[idx] if classes and idx < len(classes) else str(idx)
        confidence = float(probas[idx])
        return label, confidence, vector

    label = str(model.predict([transformed])[0])
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
        feat = _extract_enhanced_features(segment, sr)
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
    feature = _extract_enhanced_features(audio, sr)
    model = _load_model()
    label, confidence, vector = _predict_single(model, feature)
    signals = extract_audio_signals(audio, sr)
    segments = _segment_predictions(audio, sr, model, max_segments=5)
    model_classes = _get_model_classes(model)
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
