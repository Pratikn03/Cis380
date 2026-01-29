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
    parser.add_argument(
        "--grad-accum",
        type=int,
        default=1,
        help="Gradient accumulation steps (effective batch = batch_size * grad_accum).",
    )
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
        from transformers import (
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
        return dataset

    train_dataset = load_manifest(args.train_manifest)
    val_dataset = load_manifest(args.val_manifest)

    processor = WhisperProcessor.from_pretrained(
        args.model, language=args.language, task="transcribe"
    )

    # Match model dtype to device capabilities to avoid float/half mismatches.
    model_dtype = torch.float32
    if torch.cuda.is_available() and args.fp16:
        model_dtype = torch.float16
    try:
        model = WhisperForConditionalGeneration.from_pretrained(
            args.model, torch_dtype=model_dtype
        )
    except TypeError:
        model = WhisperForConditionalGeneration.from_pretrained(args.model)
        model = model.to(model_dtype)

    rng = np.random.default_rng(args.augment_seed)

    def add_noise(audio_array: "np.ndarray", snr_db: float) -> "np.ndarray":
        signal_power = np.mean(audio_array**2)
        if signal_power <= 0:
            return audio_array
        noise_power = signal_power / (10 ** (snr_db / 10))
        noise = rng.normal(0.0, np.sqrt(noise_power), size=audio_array.shape)
        return audio_array + noise

    try:
        import soundfile as sf
    except Exception as exc:
        raise SystemExit(
            "soundfile is required for STT training. Install with: pip install soundfile"
        ) from exc

    try:
        import librosa
    except Exception:
        librosa = None

    def load_audio(path: str) -> tuple["np.ndarray", int]:
        audio_array, sr = sf.read(path)
        if audio_array.ndim > 1:
            audio_array = np.mean(audio_array, axis=1)
        if sr != 16000:
            if librosa is None:
                raise SystemExit("librosa is required to resample non-16k audio.")
            audio_array = librosa.resample(audio_array, orig_sr=sr, target_sr=16000)
            sr = 16000
        return audio_array.astype("float32"), sr

    def prepare_batch(batch):
        audio_path = batch["audio"]
        audio_array, sr = load_audio(audio_path)
        audio_array = np.asarray(audio_array, dtype=np.float32)
        if args.augment and rng.random() < args.noise_prob:
            snr = rng.uniform(args.noise_min_snr, args.noise_max_snr)
            audio_array = add_noise(audio_array, snr)
        inputs = processor.feature_extractor(audio_array, sampling_rate=sr)
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

    try:
        from transformers import DataCollatorSpeechSeq2SeqWithPadding

        data_collator = DataCollatorSpeechSeq2SeqWithPadding(processor=processor)
    except Exception:
        import torch

        class DataCollatorSpeechSeq2SeqWithPadding:
            """Minimal speech collator compatible with Transformers 5.x."""

            def __init__(self, processor):
                self.processor = processor

            def __call__(self, features):
                input_features = [{"input_features": f["input_features"]} for f in features]
                batch = self.processor.feature_extractor.pad(
                    input_features, return_tensors="pt"
                )
                label_features = [{"input_ids": f["labels"]} for f in features]
                labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")
                labels = labels_batch["input_ids"].masked_fill(
                    labels_batch["attention_mask"].ne(1), -100
                )
                batch["labels"] = labels
                return batch

        data_collator = DataCollatorSpeechSeq2SeqWithPadding(processor)

    device_label = (
        "cuda"
        if torch.cuda.is_available()
        else "mps"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
        else "cpu"
    )
    print(f"[stt_train] device={device_label}")

    training_kwargs = {
        "output_dir": str(args.output_dir),
        "per_device_train_batch_size": args.batch_size,
        "per_device_eval_batch_size": args.batch_size,
        "gradient_accumulation_steps": max(1, int(args.grad_accum)),
        "learning_rate": args.learning_rate,
        "num_train_epochs": args.epochs,
        "max_steps": args.max_steps if args.max_steps > 0 else 0,
        "fp16": args.fp16 and torch.cuda.is_available(),
        "save_steps": args.save_steps,
        "eval_steps": args.eval_steps,
        "logging_steps": 50,
        "save_total_limit": 2,
        "predict_with_generate": True,
        "generation_max_length": 128,
        "report_to": "none",
    }

    import inspect

    training_sig = inspect.signature(Seq2SeqTrainingArguments.__init__)
    if "evaluation_strategy" in training_sig.parameters:
        training_kwargs["evaluation_strategy"] = "steps"
    elif "eval_strategy" in training_sig.parameters:
        training_kwargs["eval_strategy"] = "steps"

    filtered_kwargs = {
        key: value for key, value in training_kwargs.items() if key in training_sig.parameters
    }
    training_args = Seq2SeqTrainingArguments(**filtered_kwargs)

    trainer_kwargs = {
        "model": model,
        "args": training_args,
        "train_dataset": train_dataset,
        "eval_dataset": val_dataset,
        "data_collator": data_collator,
    }
    trainer_sig = inspect.signature(Seq2SeqTrainer.__init__)
    if "tokenizer" in trainer_sig.parameters:
        trainer_kwargs["tokenizer"] = processor.feature_extractor
    elif "processing_class" in trainer_sig.parameters:
        trainer_kwargs["processing_class"] = processor

    trainer = Seq2SeqTrainer(**trainer_kwargs)

    trainer.train()
    trainer.save_model(str(args.output_dir))
    processor.save_pretrained(str(args.output_dir))

    print(f"[stt_train] Saved model to {args.output_dir}")


if __name__ == "__main__":
    main()
