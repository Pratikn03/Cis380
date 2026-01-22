"""
Voice emotion prediction module.
"""

import joblib
import numpy as np
import os
import tempfile
from pathlib import Path
from app.models.voice.features import (
    load_audio,
    extract_mfcc,
    compute_zero_crossing_rate,
    compute_rms,
)

MODEL_PATH = Path("models/voice_emotion.pkl")


def predict_emotion(audio_bytes: bytes, filename: str = "audio.wav") -> dict:
    if not MODEL_PATH.exists():
        return {
            "emotion": "unknown",
            "confidence": 0.0,
            "filename": filename,
            "error": "Model not found. Run training script first.",
        }

    try:
        # Load model (in production, this should be cached globally)
        clf = joblib.load(MODEL_PATH)

        # Write bytes to temp file for librosa
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            y, sr = load_audio(tmp_path)
            if len(y) == 0:
                return {"emotion": "error", "confidence": 0.0, "error": "Empty audio"}

            mfcc = extract_mfcc(y, sr)
            zcr = compute_zero_crossing_rate(y)
            rms_mean, rms_std = compute_rms(y)

            feat_vector = np.concatenate([mfcc, [zcr, rms_mean, rms_std]]).reshape(1, -1)

            if np.isnan(feat_vector).any():
                return {"emotion": "error", "confidence": 0.0, "error": "Features contain NaN"}

            probs = clf.predict_proba(feat_vector)[0]
            classes = clf.classes_

            best_idx = np.argmax(probs)
            emotion = classes[best_idx]
            confidence = float(probs[best_idx])

            return {"emotion": emotion, "confidence": confidence, "filename": filename}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception as e:
        return {"emotion": "error", "confidence": 0.0, "error": str(e)}
