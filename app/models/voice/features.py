from __future__ import annotations

import io
from pathlib import Path
import wave

import numpy as np

try:
    import librosa  # type: ignore

    HAS_LIBROSA = True
except Exception:  # pragma: no cover
    # librosa can fail to import at runtime if optional deps (e.g., numba) are
    # incompatible with the current NumPy/Python version.
    HAS_LIBROSA = False
    librosa = None  # type: ignore[assignment]


def _librosa_ok() -> bool:
    """Return True only if librosa can actually be used at runtime.

    librosa uses lazy imports; under some Python/NumPy combos it may import but
    fail when accessing submodules (e.g. numba incompatibilities). We treat that
    as unavailable and fall back to the built-in wave loader.
    """
    global HAS_LIBROSA
    if not HAS_LIBROSA or librosa is None:
        return False
    try:
        # Touch a commonly-used attribute to force lazy imports.
        _ = librosa.load  # type: ignore[attr-defined]
        return True
    except Exception:
        HAS_LIBROSA = False
        return False

DEFAULT_SR = 22050
MFCC_COUNT = 13


def load_audio(source: bytes | Path | str, sr: int = DEFAULT_SR) -> tuple[np.ndarray, int]:
    if _librosa_ok():
        global HAS_LIBROSA
        try:
            if isinstance(source, (Path, str)):
                filepath = str(source)
                audio, rate = librosa.load(filepath, sr=sr)  # type: ignore[union-attr]
            else:
                buffer = io.BytesIO(source)
                audio, rate = librosa.load(buffer, sr=sr)  # type: ignore[union-attr]
            return audio, rate
        except Exception:  # pragma: no cover
            HAS_LIBROSA = False
    if isinstance(source, (Path, str)):
        filepath = str(source)
        reader = wave.open(filepath, "rb")
    else:
        reader = wave.open(io.BytesIO(source), "rb")
    n_frames = reader.getnframes()
    frames = reader.readframes(n_frames)
    dtype = np.int16 if reader.getsampwidth() == 2 else np.int8
    audio = np.frombuffer(frames, dtype=dtype).astype(np.float32)
    # Normalize PCM to roughly [-1, 1] for stable downstream features.
    if dtype == np.int16:
        audio /= 32768.0
    elif dtype == np.int8:
        audio /= 128.0
    rate = reader.getframerate()
    reader.close()
    return audio, rate


def extract_mfcc(audio: np.ndarray, sr: int) -> np.ndarray:
    if _librosa_ok():
        global HAS_LIBROSA
        try:
            mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=MFCC_COUNT)  # type: ignore[union-attr]
            means = np.mean(mfcc, axis=1)
            stds = np.std(mfcc, axis=1)
            return np.concatenate([means, stds])
        except Exception:  # pragma: no cover
            HAS_LIBROSA = False
    means = np.mean(audio)
    stds = np.std(audio)
    feature = np.array([means, stds] * MFCC_COUNT)
    return feature


def compute_zero_crossing_rate(audio: np.ndarray) -> float:
    """Return the mean zero-crossing rate (ZCR)."""
    if audio.size == 0:
        return 0.0
    if _librosa_ok():
        global HAS_LIBROSA
        try:
            zcr = librosa.feature.zero_crossing_rate(y=audio)  # type: ignore[union-attr]
            return float(np.mean(zcr))
        except Exception:  # pragma: no cover
            HAS_LIBROSA = False
    # Fallback: sign-change ratio.
    signs = np.sign(audio)
    changes = np.sum(signs[:-1] != signs[1:])
    return float(changes / max(1, audio.size - 1))


def compute_rms(audio: np.ndarray) -> tuple[float, float]:
    """Return (mean, std) of RMS energy."""
    if audio.size == 0:
        return 0.0, 0.0
    if _librosa_ok():
        global HAS_LIBROSA
        try:
            rms = librosa.feature.rms(y=audio).flatten()  # type: ignore[union-attr]
            return float(np.mean(rms)), float(np.std(rms))
        except Exception:  # pragma: no cover
            HAS_LIBROSA = False
    # Fallback: RMS on the whole signal.
    rms = float(np.sqrt(np.mean(np.square(audio))))
    return rms, 0.0


def compute_spectral_contrast(audio: np.ndarray, sr: int) -> float | None:
    """Return mean spectral contrast if available."""
    if audio.size == 0:
        return 0.0
    if not _librosa_ok():
        return None
    global HAS_LIBROSA
    try:
        contrast = librosa.feature.spectral_contrast(y=audio, sr=sr)  # type: ignore[union-attr]
        return float(np.mean(contrast))
    except Exception:  # pragma: no cover
        HAS_LIBROSA = False
        return None


def compute_pitch(audio: np.ndarray, sr: int) -> tuple[float | None, float | None]:
    """Return (mean, std) pitch estimate (Hz) if available."""
    if audio.size == 0:
        return None, None
    if not _librosa_ok():
        return None, None
    global HAS_LIBROSA
    try:
        f0 = librosa.yin(audio, fmin=50.0, fmax=400.0, sr=sr)  # type: ignore[union-attr]
    except Exception:
        HAS_LIBROSA = False
        return None, None
    f0 = np.asarray(f0)
    f0 = f0[np.isfinite(f0)]
    if f0.size == 0:
        return None, None
    return float(np.mean(f0)), float(np.std(f0))


def extract_audio_signals(audio: np.ndarray, sr: int) -> dict[str, float | str | None]:
    """Compute lightweight, offline-friendly audio signals (non-model features)."""
    duration_sec = float(audio.size / max(1, sr))
    zcr_mean = compute_zero_crossing_rate(audio)
    rms_mean, rms_std = compute_rms(audio)
    pitch_mean, pitch_std = compute_pitch(audio, sr)
    spectral_contrast_mean = compute_spectral_contrast(audio, sr)

    # Simple heuristic stress score (0..1). This is NOT clinical; it's just a demo signal.
    parts: list[float] = []
    parts.append(min(max(zcr_mean / 0.15, 0.0), 1.0))
    parts.append(min(max(rms_mean / 0.2, 0.0), 1.0))
    if pitch_std is not None:
        parts.append(min(max(pitch_std / 50.0, 0.0), 1.0))
    stress_score = float(sum(parts) / max(1, len(parts)))

    return {
        "sample_rate": float(sr),
        "duration_sec": round(duration_sec, 4),
        "zcr_mean": round(float(zcr_mean), 6),
        "rms_mean": round(float(rms_mean), 6),
        "rms_std": round(float(rms_std), 6),
        "pitch_mean_hz": None if pitch_mean is None else round(float(pitch_mean), 4),
        "pitch_std_hz": None if pitch_std is None else round(float(pitch_std), 4),
        "spectral_contrast_mean": None
        if spectral_contrast_mean is None
        else round(float(spectral_contrast_mean), 6),
        "stress_score_heuristic": round(stress_score, 4),
        "stress_note": "Heuristic only; not clinically validated.",
    }
