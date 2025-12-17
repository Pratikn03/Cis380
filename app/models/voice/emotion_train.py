from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List

import joblib
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split

# Allow running via `python app/models/voice/emotion_train.py` from repo root.
if __package__ in {None, ""}:
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from app.models.voice.features import extract_mfcc, load_audio

MODEL_PATH = Path("models/voice_emotion.pkl")
RAW_DIR = Path("data/raw/voice")
SUPPORTED = ["happy", "sad", "angry", "neutral", "fearful"]


def _synthetic_rows(label: str, n: int) -> List[Dict[str, float]]:
    rng = np.random.default_rng(42)
    mean = 0.0 if label == "neutral" else 1.0
    rows: List[Dict[str, float]] = []
    for _ in range(max(0, int(n))):
        values = rng.normal(loc=mean, scale=0.5, size=26)
        row = {f"f{i}": float(values[i]) for i in range(len(values))}
        row["label"] = label
        rows.append(row)
    return rows


def gather_features(*, limit_per_class: int | None = None, min_per_class: int = 25) -> List[Dict[str, float]]:
    data = []
    for label in SUPPORTED:
        folder = RAW_DIR / label
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
                feature = extract_mfcc(audio, sr)
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
            values = np.random.normal(loc=0.0 if label == "neutral" else 1.0, scale=0.5, size=26)
            summary = {f"f{i}": float(values[i]) for i in range(len(values))}
            summary["label"] = label
            data.append(summary)
    return data


def train_model(data: List[Dict[str, float]]) -> None:
    features = []
    labels = []
    for entry in data:
        lbl = entry.pop("label")
        labels.append(lbl)
        features.append([entry[f"f{i}"] for i in range(26)])
    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)
    clf = MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=200, random_state=42)
    clf.fit(X_train, y_train)
    acc = clf.score(X_test, y_test)
    print(f"Trained voice emotion model (acc={acc:.2f})")
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, MODEL_PATH)


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
    args = parser.parse_args()

    limit = None if (args.limit_per_class is None or args.limit_per_class <= 0) else int(args.limit_per_class)
    data = gather_features(limit_per_class=limit, min_per_class=max(1, int(args.min_per_class)))
    train_model(data)


if __name__ == "__main__":
    main()
