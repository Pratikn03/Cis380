from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.stt.stt_utils import normalize_text  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tune Whisper on local STT dataset.")
    parser.add_argument(
        "--train-manifest",
        type=Path,
        default=Path("data/raw/stt/manifest.train.csv"),
        help="Train manifest CSV.",
    )
    parser.add_argument(
        "--val-manifest",
        type=Path,
        default=Path("data/raw/stt/manifest.val.csv"),
        help="Validation manifest CSV.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="openai/whisper-small",
        help="Hugging Face model name or path.",
    )
    parser.add_argument("--language", type=str, default="en", help="Language code.")
    parser.add_argument("--output-dir", type=Path, default=Path("models/whisper_stt"))
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=1e-5)
    parser.add_argument("--max-steps", type=int, default=0)
    parser.add_argument("--fp16", action="store_true", help="Enable fp16 if supported.")
    parser.add_argument("--normalize", action="store_true", help="Normalize transcript text.")
    parser.add_argument(
        "--augment",
        action="store_true",
        help="Apply noise augmentation during training.",
    )
    parser.add_argument(
        "--noise-prob",
        type=float,
        default=0.5,
        help="Probability of adding noise to a sample.",
    )
    parser.add_argument(
        "--noise-min-snr",
        type=float,
        default=10.0,
        help="Minimum SNR (dB) for noise augmentation.",
    )
    parser.add_argument(
        "--noise-max-snr",
        type=float,
        default=25.0,
        help="Maximum SNR (dB) for noise augmentation.",
    )
    parser.add_argument(
        "--augment-seed",
        type=int,
        default=42,
        help="Seed for augmentation randomness.",
    )
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--save-steps", type=int, default=200)
    parser.add_argument("--eval-steps", type=int, default=200)
    return parser.parse_args()


def main() -> None:
    try:
        import datasets
        import numpy as np
        import torch
        from datasets import Audio
        from transformers import (
            DataCollatorSpeechSeq2SeqWithPadding,
            Seq2SeqTrainer,
            Seq2SeqTrainingArguments,
            WhisperForConditionalGeneration,
            WhisperProcessor,
        )
    except ImportError as exc:
        raise SystemExit(
            "Missing dependencies. Install optional STT packages:\n"
            "  pip install -r requirements-optional.txt\n"
            "  pip install datasets transformers accelerate soundfile\n"
        ) from exc

    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    if not args.train_manifest.exists():
        raise SystemExit(f"Train manifest not found: {args.train_manifest}")
    if not args.val_manifest.exists():
        raise SystemExit(f"Val manifest not found: {args.val_manifest}")

    def load_manifest(path: Path) -> datasets.Dataset:
        dataset = datasets.load_dataset("csv", data_files=str(path), split="train")
        dataset = dataset.rename_column("audio_path", "audio")

        base_dir = PROJECT_ROOT

        def make_abs(batch):
            return {"audio": str((base_dir / batch["audio"]).resolve())}

        dataset = dataset.map(make_abs)
        dataset = dataset.cast_column("audio", Audio(sampling_rate=16000))
        return dataset

    train_dataset = load_manifest(args.train_manifest)
    val_dataset = load_manifest(args.val_manifest)

    processor = WhisperProcessor.from_pretrained(
        args.model, language=args.language, task="transcribe"
    )
    model = WhisperForConditionalGeneration.from_pretrained(args.model)

    rng = np.random.default_rng(args.augment_seed)

    def add_noise(audio_array: "np.ndarray", snr_db: float) -> "np.ndarray":
        signal_power = np.mean(audio_array**2)
        if signal_power <= 0:
            return audio_array
        noise_power = signal_power / (10 ** (snr_db / 10))
        noise = rng.normal(0.0, np.sqrt(noise_power), size=audio_array.shape)
        return audio_array + noise

    def prepare_batch(batch):
        audio = batch["audio"]
        audio_array = audio["array"]
        if args.augment and rng.random() < args.noise_prob:
            snr = rng.uniform(args.noise_min_snr, args.noise_max_snr)
            audio_array = add_noise(audio_array, snr)
        inputs = processor.feature_extractor(audio_array, sampling_rate=audio["sampling_rate"])
        batch["input_features"] = inputs.input_features[0]
        text = batch["text"] or ""
        if args.normalize:
            text = normalize_text(text)
        batch["labels"] = processor.tokenizer(text).input_ids
        return batch

    train_dataset = train_dataset.map(
        prepare_batch,
        remove_columns=train_dataset.column_names,
        num_proc=args.num_workers,
    )
    val_dataset = val_dataset.map(
        prepare_batch,
        remove_columns=val_dataset.column_names,
        num_proc=args.num_workers,
    )

    data_collator = DataCollatorSpeechSeq2SeqWithPadding(processor=processor)

    training_args = Seq2SeqTrainingArguments(
        output_dir=str(args.output_dir),
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        num_train_epochs=args.epochs,
        max_steps=args.max_steps if args.max_steps > 0 else None,
        fp16=args.fp16 and torch.cuda.is_available(),
        evaluation_strategy="steps",
        save_steps=args.save_steps,
        eval_steps=args.eval_steps,
        logging_steps=50,
        save_total_limit=2,
        predict_with_generate=True,
        generation_max_length=128,
        report_to="none",
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
        tokenizer=processor.feature_extractor,
    )

    trainer.train()
    trainer.save_model(str(args.output_dir))
    processor.save_pretrained(str(args.output_dir))

    print(f"[stt_train] Saved model to {args.output_dir}")


if __name__ == "__main__":
    main()
