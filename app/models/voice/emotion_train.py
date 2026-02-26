from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split

# Allow running via `python app/models/voice/emotion_train.py` from repo root.
if __package__ in {None, ""}:
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from app.models.voice.features import (
    compute_pitch,
    compute_rms,
    compute_spectral_contrast,
    compute_zero_crossing_rate,
    extract_mfcc,
    load_audio,
)

MODEL_PATH = Path("models/voice_emotion.pkl")
RAW_DIR = Path("data/raw/voice")
BALANCED_DIR = Path("data/processed/voice_balanced")
SUPPORTED = ["happy", "sad", "angry", "neutral", "fearful"]
# 26 MFCC + 5 additional features (zcr, rms_mean, rms_std, pitch_mean, spectral_contrast)
FEATURE_COUNT = 31


def _synthetic_rows(label: str, n: int) -> List[Dict[str, float]]:
    rng = np.random.default_rng(42)
    mean = 0.0 if label == "neutral" else 1.0
    rows: List[Dict[str, float]] = []
    for _ in range(max(0, int(n))):
        values = rng.normal(loc=mean, scale=0.5, size=FEATURE_COUNT)
        row = {f"f{i}": float(values[i]) for i in range(len(values))}
        row["label"] = label
        rows.append(row)
    return rows


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
    extra_features = np.array(
        [
            zcr,
            rms_mean,
            rms_std,
            pitch_mean if pitch_mean is not None else 0.0,
            spectral if spectral is not None else 0.0,
        ],
        dtype=np.float64,
    )

    return np.concatenate([mfcc_feat, extra_features])


def gather_features(
    *,
    data_root: Path = RAW_DIR,
    limit_per_class: int | None = None,
    min_per_class: int = 25,
) -> List[Dict[str, float]]:
    data = []
    for label in SUPPORTED:
        folder = data_root / label
        kept = 0
        if not folder.exists():
            data.extend(_synthetic_rows(label, min_per_class))
            continue

        files = sorted(folder.glob("*.wav")) or sorted(folder.glob("*.*"))
        if limit_per_class is not None and limit_per_class > 0:
            files = files[:limit_per_class]
        for audio_file in files:
            try:
                audio, sr = load_audio(audio_file)
                feature = _extract_enhanced_features(audio, sr)
                summary = {f"f{i}": float(feature[i]) for i in range(len(feature))}
                summary["label"] = label
                data.append(summary)
                kept += 1
            except Exception:
                continue

        # Guarantee class presence even if a local folder is missing or empty.
        if kept < min_per_class:
            data.extend(_synthetic_rows(label, min_per_class - kept))

    return data


def synthetic_data() -> List[Dict[str, float]]:
    np.random.seed(42)
    data = []
    for label in SUPPORTED:
        for _ in range(10):
            values = np.random.normal(
                loc=0.0 if label == "neutral" else 1.0, scale=0.5, size=FEATURE_COUNT
            )
            summary = {f"f{i}": float(values[i]) for i in range(len(values))}
            summary["label"] = label
            data.append(summary)
    return data


def train_model(
    data: List[Dict[str, float]],
    *,
    out_model: Path = MODEL_PATH,
    seed: int = 42,
    n_estimators: int = 200,
    max_depth: int = 25,
) -> None:
    features = []
    labels = []
    for entry in data:
        lbl = entry.pop("label")
        labels.append(lbl)
        features.append([entry[f"f{i}"] for i in range(FEATURE_COUNT)])

    # Convert to numpy and handle NaN/Inf values
    X = np.array(features, dtype=np.float64)
    y = np.array(labels)

    # Filter out rows with NaN or Inf values
    valid_mask = np.all(np.isfinite(X), axis=1)
    X = X[valid_mask]
    y = y[valid_mask]
    print(f"📊 Using {len(X)} valid samples (filtered {(~valid_mask).sum()} bad samples)")
    print(f"📊 Features per sample: {FEATURE_COUNT} (26 MFCC + 5 audio features)")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=int(seed), stratify=y
    )

    # Use Pipeline with StandardScaler + RandomForest for robustness
    clf = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "rf",
                RandomForestClassifier(
                    n_estimators=max(10, int(n_estimators)),
                    max_depth=max(2, int(max_depth)),
                    random_state=int(seed),
                    n_jobs=-1,
                ),
            ),
        ]
    )
    clf.fit(X_train, y_train)
    acc = clf.score(X_test, y_test)
    print(f"✅ Trained voice emotion model (accuracy={acc:.2%})")
    out_model.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, out_model)
    print(f"📁 Saved to {out_model}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the voice emotion model.")
    parser.add_argument(
        "--limit-per-class",
        type=int,
        default=500,
        help="Max audio files per class to process (0 uses all).",
    )
    parser.add_argument(
        "--min-per-class",
        type=int,
        default=25,
        help="Minimum samples per class (pads missing classes with synthetic rows to guarantee label support).",
    )
    parser.add_argument(
        "--out-model",
        type=Path,
        default=MODEL_PATH,
        help="Output model artifact path.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic splits/model fit.",
    )
    parser.add_argument(
        "--n-estimators",
        type=int,
        default=200,
        help="RandomForest trees (voice model is non-epoch based).",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=25,
        help="RandomForest max depth.",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=None,
        help="Voice dataset root. Defaults to data/processed/voice_balanced when available, otherwise data/raw/voice.",
    )
    args = parser.parse_args()

    limit = (
        None if (args.limit_per_class is None or args.limit_per_class <= 0) else int(args.limit_per_class)
    )
    data_root = args.data_root or (BALANCED_DIR if BALANCED_DIR.exists() else RAW_DIR)
    print(f"🎙️ Using voice data root: {data_root}")
    data = gather_features(
        data_root=data_root,
        limit_per_class=limit,
        min_per_class=max(1, int(args.min_per_class)),
    )
    train_model(
        data,
        out_model=args.out_model,
        seed=int(args.seed),
        n_estimators=int(args.n_estimators),
        max_depth=int(args.max_depth),
    )


if __name__ == "__main__":
    main()
