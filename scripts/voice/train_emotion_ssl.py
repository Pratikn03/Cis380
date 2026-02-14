from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score

# Allow running directly from repo root.
if __package__ in {None, ""}:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from scripts.voice.ssl_utils import AudioDataCollator, build_label_maps, load_manifest, prepare_dataset


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Train SSL-based voice emotion classifier.")
    ap.add_argument("--train-manifest", type=Path, required=True)
    ap.add_argument("--val-manifest", type=Path, required=True)
    ap.add_argument("--model", type=str, default="facebook/wav2vec2-base")
    ap.add_argument("--output-dir", type=Path, default=Path("models/voice_emotion_ssl"))
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--grad-accum", type=int, default=1)
    ap.add_argument("--learning-rate", type=float, default=1e-4)
    ap.add_argument("--num-workers", type=int, default=2)
    ap.add_argument("--save-steps", type=int, default=200)
    ap.add_argument("--eval-steps", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--freeze-feature-encoder", action="store_true", default=True)
    ap.add_argument("--no-freeze-feature-encoder", dest="freeze_feature_encoder", action="store_false")
    ap.add_argument("--use-class-weights", action="store_true", default=False)
    ap.add_argument("--max-steps", type=int, default=0)
    ap.add_argument("--resume-from-checkpoint", type=str, default=None)
    return ap.parse_args()


def main() -> None:
    try:
        import torch
        from transformers import (
            AutoFeatureExtractor,
            AutoModelForAudioClassification,
            Trainer,
            TrainingArguments,
        )
    except ImportError as exc:
        raise SystemExit(
            "Missing dependencies. Install optional packages:\n"
            "  pip install -r requirements-optional.txt\n"
            "  pip install transformers datasets torchaudio soundfile\n"
        ) from exc

    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    train_df = load_manifest(args.train_manifest)
    val_df = load_manifest(args.val_manifest)

    label2id, id2label = build_label_maps(train_df)

    feature_extractor = AutoFeatureExtractor.from_pretrained(args.model)
    train_ds = prepare_dataset(train_df, feature_extractor, label2id, args.num_workers)
    val_ds = prepare_dataset(val_df, feature_extractor, label2id, args.num_workers)

    model = AutoModelForAudioClassification.from_pretrained(
        args.model,
        num_labels=len(label2id),
        label2id=label2id,
        id2label=id2label,
    )

    if args.freeze_feature_encoder and hasattr(model, "freeze_feature_encoder"):
        model.freeze_feature_encoder()

    class_weights = None
    if args.use_class_weights:
        from sklearn.utils.class_weight import compute_class_weight

        labels = train_df["label"].map(label2id).to_numpy()
        weights = compute_class_weight(class_weight="balanced", classes=np.arange(len(label2id)), y=labels)
        class_weights = torch.tensor(weights, dtype=torch.float32)

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=-1)
        return {
            "accuracy": accuracy_score(labels, preds),
            "macro_f1": f1_score(labels, preds, average="macro"),
            "uar": balanced_accuracy_score(labels, preds),
        }

    class WeightedTrainer(Trainer):
        def __init__(self, *args, class_weights=None, **kwargs):
            super().__init__(*args, **kwargs)
            self.class_weights = class_weights

        def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
            labels = inputs.pop("labels")
            outputs = model(**inputs)
            logits = outputs.logits
            loss_fn = torch.nn.CrossEntropyLoss(weight=self.class_weights)
            loss = loss_fn(logits, labels)
            return (loss, outputs) if return_outputs else loss

    training_kwargs = {
        "output_dir": str(args.output_dir),
        "per_device_train_batch_size": args.batch_size,
        "per_device_eval_batch_size": args.batch_size,
        "gradient_accumulation_steps": max(1, int(args.grad_accum)),
        "learning_rate": args.learning_rate,
        "num_train_epochs": args.epochs,
        "max_steps": args.max_steps if args.max_steps > 0 else -1,
        "save_steps": args.save_steps,
        "eval_steps": args.eval_steps,
        "logging_steps": 50,
        "save_total_limit": 2,
        "load_best_model_at_end": True,
        "metric_for_best_model": "macro_f1",
        "report_to": "none",
        "fp16": torch.cuda.is_available(),
        "seed": args.seed,
    }

    import inspect

    sig = inspect.signature(TrainingArguments.__init__)
    if "evaluation_strategy" in sig.parameters:
        training_kwargs["evaluation_strategy"] = "steps"
    elif "eval_strategy" in sig.parameters:
        training_kwargs["eval_strategy"] = "steps"

    filtered_kwargs = {k: v for k, v in training_kwargs.items() if k in sig.parameters}
    training_args = TrainingArguments(**filtered_kwargs)

    trainer_kwargs = {
        "model": model,
        "args": training_args,
        "train_dataset": train_ds,
        "eval_dataset": val_ds,
        "data_collator": AudioDataCollator(feature_extractor),
        "compute_metrics": compute_metrics,
        "class_weights": class_weights,
    }
    import inspect

    trainer_sig = inspect.signature(Trainer.__init__)
    if "tokenizer" in trainer_sig.parameters:
        trainer_kwargs["tokenizer"] = feature_extractor
    elif "processing_class" in trainer_sig.parameters:
        trainer_kwargs["processing_class"] = feature_extractor

    trainer = WeightedTrainer(**trainer_kwargs)

    trainer.train(resume_from_checkpoint=args.resume_from_checkpoint)
    trainer.save_model(str(args.output_dir))
    feature_extractor.save_pretrained(str(args.output_dir))

    meta = {
        "label2id": label2id,
        "id2label": id2label,
        "model": args.model,
    }
    (args.output_dir / "label_map.json").write_text(json.dumps(meta, indent=2))
    print(f"[voice-ssl] saved model to {args.output_dir}")


if __name__ == "__main__":
    main()
