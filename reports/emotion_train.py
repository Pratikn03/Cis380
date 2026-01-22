"""
Train a voice emotion classifier using Random Forest.
"""

import argparse
import joblib
import numpy as np
import os
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from app.models.voice.features import (
    load_audio,
    extract_mfcc,
    compute_zero_crossing_rate,
    compute_rms,
)


def main():
    parser = argparse.ArgumentParser(description="Train voice emotion model")
    parser.add_argument(
        "--data-dir", default="data/raw/voice", help="Directory containing emotion subfolders"
    )
    parser.add_argument("--out-model", default="models/voice_emotion.pkl", help="Output model path")
    parser.add_argument(
        "--limit-per-class", type=int, default=0, help="Limit samples per class for faster training"
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"Data directory {data_dir} not found.")
        return

    features = []
    labels = []

    # Expected structure: data/raw/voice/{emotion}/*.wav
    # e.g. data/raw/voice/happy/001.wav
    for emotion_dir in data_dir.iterdir():
        if not emotion_dir.is_dir():
            continue

        emotion = emotion_dir.name
        files = list(emotion_dir.glob("*.wav"))
        if args.limit_per_class > 0:
            files = files[: args.limit_per_class]

        print(f"Processing {emotion}: {len(files)} files")

        for wav_file in files:
            try:
                y, sr = load_audio(str(wav_file))
                if len(y) == 0:
                    continue

                mfcc = extract_mfcc(y, sr)
                zcr = compute_zero_crossing_rate(y)
                rms_mean, rms_std = compute_rms(y)

                feat_vector = np.concatenate([mfcc, [zcr, rms_mean, rms_std]])
                features.append(feat_vector)
                labels.append(emotion)
            except Exception as e:
                print(f"Error processing {wav_file}: {e}")

    if not features:
        print("No features extracted. Check data directory structure.")
        return

    X = np.array(features)
    y = np.array(labels)

    # Remove NaNs if any
    valid_idx = ~np.isnan(X).any(axis=1)
    X = X[valid_idx]
    y = y[valid_idx]

    print(f"Training on {len(X)} samples with {X.shape[1]} features.")

    clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    clf.fit(X, y)

    Path(args.out_model).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, args.out_model)
    print(f"Model saved to {args.out_model}")


if __name__ == "__main__":
    main()
