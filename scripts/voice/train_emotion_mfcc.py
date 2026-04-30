from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler

if __package__ in {None, ""}:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from app.models.voice.emotion_train import FEATURE_COUNT, _extract_enhanced_features
from app.models.voice.features import load_audio
from scripts.voice.ssl_utils import load_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train API-backed MFCC voice emotion model.")
    parser.add_argument("--train-manifest", type=Path, required=True)
    parser.add_argument("--val-manifest", type=Path, required=True)
    parser.add_argument("--output-model", type=Path, default=Path("models/voice_emotion.pkl"))
    parser.add_argument("--metrics-out", type=Path, default=Path("reports/voice_emotion_train.json"))
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--rf-estimators", type=int, default=600)
    parser.add_argument("--rf-max-depth", type=int, default=32)
    return parser.parse_args()


def extract_manifest_features(manifest: Path) -> tuple[np.ndarray, np.ndarray]:
    rows = load_manifest(manifest)
    features: list[np.ndarray] = []
    labels: list[str] = []
    skipped = 0
    for row in rows.itertuples(index=False):
        try:
            audio, sr = load_audio(Path(str(row.path)))
            feature = _extract_enhanced_features(audio, sr)
        except Exception:
            skipped += 1
            continue
        if feature.shape[0] != FEATURE_COUNT or not np.all(np.isfinite(feature)):
            skipped += 1
            continue
        features.append(feature.astype(np.float64))
        labels.append(str(row.label))
    if not features:
        raise SystemExit(f"no valid voice features extracted from {manifest}")
    print(f"[voice-mfcc] {manifest} samples={len(features)} skipped={skipped}")
    return np.vstack(features), np.asarray(labels)


def metrics_for(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
        "uar": float(balanced_accuracy_score(y_true, y_pred)),
    }


def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(int(args.seed))

    X_train_raw, y_train_raw = extract_manifest_features(args.train_manifest)
    X_val_raw, y_val_raw = extract_manifest_features(args.val_manifest)

    label_encoder = LabelEncoder()
    y_train = label_encoder.fit_transform(y_train_raw)
    y_val = label_encoder.transform(y_val_raw)

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train_raw)
    X_val = scaler.transform(X_val_raw)

    classes = np.arange(len(label_encoder.classes_))
    mlp = MLPClassifier(
        hidden_layer_sizes=(256, 128, 64),
        activation="relu",
        solver="adam",
        alpha=1e-4,
        batch_size=max(1, int(args.batch_size)),
        learning_rate_init=1e-3,
        max_iter=1,
        warm_start=True,
        random_state=int(args.seed),
        shuffle=False,
    )

    best: dict[str, object] = {"name": "mlp", "score": -1.0, "model": None, "metrics": {}}
    for epoch in range(1, int(args.epochs) + 1):
        order = rng.permutation(len(X_train))
        mlp.partial_fit(X_train[order], y_train[order], classes=classes)
        pred = mlp.predict(X_val)
        epoch_metrics = metrics_for(y_val, pred)
        score = epoch_metrics["macro_f1"]
        if score > float(best["score"]):
            best = {
                "name": "mlp",
                "score": score,
                "model": copy.deepcopy(mlp),
                "metrics": epoch_metrics,
                "epoch": epoch,
            }
        if epoch == 1 or epoch % 5 == 0 or epoch == int(args.epochs):
            print(
                "[voice-mfcc] "
                f"epoch={epoch}/{args.epochs} "
                f"macro_f1={epoch_metrics['macro_f1']:.4f} "
                f"uar={epoch_metrics['uar']:.4f} "
                f"accuracy={epoch_metrics['accuracy']:.4f}"
            )

    rf = RandomForestClassifier(
        n_estimators=max(50, int(args.rf_estimators)),
        max_depth=max(2, int(args.rf_max_depth)),
        class_weight="balanced_subsample",
        random_state=int(args.seed),
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    rf_metrics = metrics_for(y_val, rf.predict(X_val))
    print(
        "[voice-mfcc] random_forest "
        f"macro_f1={rf_metrics['macro_f1']:.4f} "
        f"uar={rf_metrics['uar']:.4f} "
        f"accuracy={rf_metrics['accuracy']:.4f}"
    )
    if rf_metrics["macro_f1"] > float(best["score"]):
        best = {
            "name": "random_forest",
            "score": rf_metrics["macro_f1"],
            "model": rf,
            "metrics": rf_metrics,
            "epoch": None,
        }

    artifact = {
        "model": best["model"],
        "scaler": scaler,
        "label_encoder": label_encoder,
        "feature_count": FEATURE_COUNT,
        "backend": "mfcc_sklearn",
        "selected_model": best["name"],
    }
    args.output_model.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, args.output_model)

    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "artifact": str(args.output_model),
        "train_manifest": str(args.train_manifest),
        "val_manifest": str(args.val_manifest),
        "train_samples": int(len(X_train)),
        "val_samples": int(len(X_val)),
        "classes": [str(v) for v in label_encoder.classes_],
        "epochs": int(args.epochs),
        "selected_model": best["name"],
        "selected_epoch": best["epoch"],
        "validation": best["metrics"],
    }
    args.metrics_out.parent.mkdir(parents=True, exist_ok=True)
    args.metrics_out.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"[voice-mfcc] saved model to {args.output_model}")


if __name__ == "__main__":
    main()
