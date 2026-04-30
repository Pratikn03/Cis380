from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, f1_score

if __package__ in {None, ""}:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from app.models.voice.emotion_train import FEATURE_COUNT, _extract_enhanced_features
from app.models.voice.features import load_audio
from scripts.voice.ssl_utils import load_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate API-backed MFCC voice emotion model.")
    parser.add_argument("--model", type=Path, default=Path("models/voice_emotion.pkl"))
    parser.add_argument("--test-manifest", type=Path, required=True)
    parser.add_argument("--json-out", type=Path, default=Path("reports/voice_emotion_eval.json"))
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
    print(f"[voice-mfcc-eval] {manifest} samples={len(features)} skipped={skipped}")
    return np.vstack(features), np.asarray(labels)


def main() -> None:
    args = parse_args()
    artifact = joblib.load(args.model)
    if not isinstance(artifact, dict) or "model" not in artifact:
        raise SystemExit(f"unsupported voice artifact format: {args.model}")
    model = artifact["model"]
    scaler = artifact.get("scaler")
    label_encoder = artifact.get("label_encoder")

    X_raw, y_true_labels = extract_manifest_features(args.test_manifest)
    X = scaler.transform(X_raw) if scaler is not None else X_raw
    y_pred = model.predict(X)

    if label_encoder is not None and hasattr(label_encoder, "transform"):
        y_true = label_encoder.transform(y_true_labels)
        target_names = [str(v) for v in label_encoder.classes_]
    else:
        y_true = y_true_labels
        target_names = sorted({str(v) for v in y_true_labels})

    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
        "uar": float(balanced_accuracy_score(y_true, y_pred)),
        "artifact": str(args.model),
        "test_manifest": str(args.test_manifest),
        "test_samples": int(len(y_true)),
        "backend": str(artifact.get("backend", "mfcc_sklearn")),
        "selected_model": str(artifact.get("selected_model", type(model).__name__)),
        "report": classification_report(
            y_true,
            y_pred,
            target_names=target_names,
            output_dict=True,
            zero_division=0,
        ),
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))
    print(f"[voice-mfcc-eval] wrote {args.json_out}")


if __name__ == "__main__":
    main()
