from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, f1_score

# Allow running directly from repo root.
if __package__ in {None, ""}:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from scripts.voice.ssl_utils import AudioDataCollator, build_label_maps, load_manifest, prepare_dataset


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Evaluate SSL-based voice emotion classifier.")
    ap.add_argument("--model-dir", type=Path, required=True)
    ap.add_argument("--test-manifest", type=Path, required=True)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--num-workers", type=int, default=2)
    ap.add_argument("--json-out", type=Path, default=Path("reports/voice_emotion_eval.json"))
    return ap.parse_args()


def main() -> None:
    try:
        from transformers import AutoFeatureExtractor, AutoModelForAudioClassification, Trainer, TrainingArguments
    except ImportError as exc:
        raise SystemExit("Missing dependencies. Install transformers + datasets + torchaudio + soundfile.") from exc

    args = parse_args()
    test_df = load_manifest(args.test_manifest)
    label_map_path = args.model_dir / "label_map.json"
    if label_map_path.exists():
        meta = json.loads(label_map_path.read_text())
        label2id = {str(k): int(v) for k, v in meta.get("label2id", {}).items()}
        id2label = {int(k): str(v) for k, v in meta.get("id2label", {}).items()}
    else:
        label2id, id2label = build_label_maps(test_df)

    feature_extractor = AutoFeatureExtractor.from_pretrained(args.model_dir)
    model = AutoModelForAudioClassification.from_pretrained(
        args.model_dir,
        num_labels=len(label2id),
        label2id=label2id,
        id2label=id2label,
    )

    test_ds = prepare_dataset(test_df, feature_extractor, label2id, args.num_workers)

    training_args = TrainingArguments(
        output_dir=str(args.model_dir),
        per_device_eval_batch_size=args.batch_size,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=AudioDataCollator(feature_extractor),
        tokenizer=feature_extractor,
    )

    preds = trainer.predict(test_ds)
    logits = preds.predictions
    labels = preds.label_ids
    y_pred = np.argmax(logits, axis=-1)

    metrics = {
        "accuracy": accuracy_score(labels, y_pred),
        "macro_f1": f1_score(labels, y_pred, average="macro"),
        "uar": balanced_accuracy_score(labels, y_pred),
        "report": classification_report(labels, y_pred, target_names=[id2label[i] for i in range(len(id2label))], output_dict=True),
    }

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))
    print(f"[eval] wrote {args.json_out}")


if __name__ == "__main__":
    main()
