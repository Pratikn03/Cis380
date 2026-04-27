from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score

# Allow running directly from repo root.
if __package__ in {None, ""}:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from scripts.voice.ssl_utils import (
    AudioDataCollator,
    build_label_maps,
    load_audio,
    load_manifest,
    prepare_dataset,
)


@dataclass
class AugmentConfig:
    enabled: bool
    prob: float
    noise_std: float
    gain_min: float
    gain_max: float
    time_shift_ms: int
    time_mask_ms: int
    sampling_rate: int


class WaveformAugmenter:
    def __init__(self, config: AugmentConfig, seed: int | None = None) -> None:
        self.config = config
        self.rng = np.random.default_rng(seed)

    def __call__(self, values):
        if not self.config.enabled:
            return values
        audio = np.asarray(values, dtype=np.float32)
        if audio.size == 0:
            return values

        cfg = self.config
        if cfg.gain_min != 1.0 or cfg.gain_max != 1.0:
            if self.rng.random() < cfg.prob:
                gain = float(self.rng.uniform(cfg.gain_min, cfg.gain_max))
                audio = audio * gain

        if cfg.noise_std > 0 and self.rng.random() < cfg.prob:
            noise = self.rng.normal(0.0, cfg.noise_std, size=audio.shape).astype(np.float32)
            audio = audio + noise

        if cfg.time_shift_ms > 0 and self.rng.random() < cfg.prob:
            max_shift = int(cfg.time_shift_ms / 1000.0 * cfg.sampling_rate)
            if max_shift > 0:
                shift = int(self.rng.integers(-max_shift, max_shift + 1))
                if shift > 0:
                    audio = np.pad(audio, (shift, 0), mode="constant")[: audio.shape[0]]
                elif shift < 0:
                    audio = np.pad(audio, (0, -shift), mode="constant")[(-shift) :]

        if cfg.time_mask_ms > 0 and self.rng.random() < cfg.prob:
            mask = int(cfg.time_mask_ms / 1000.0 * cfg.sampling_rate)
            if 0 < mask < audio.shape[0]:
                start = int(self.rng.integers(0, audio.shape[0] - mask))
                audio[start : start + mask] = 0.0

        if np.max(np.abs(audio)) > 1.0:
            audio = np.clip(audio, -1.0, 1.0)

        return audio.astype(np.float32).tolist()


class AugmentingAudioDataCollator(AudioDataCollator):
    def __init__(self, feature_extractor, augmenter: WaveformAugmenter | None) -> None:
        super().__init__(feature_extractor)
        self.augmenter = augmenter

    def __call__(self, features):
        if self.augmenter is not None:
            for feature in features:
                feature["input_values"] = self.augmenter(feature["input_values"])
        return super().__call__(features)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Train SSL-based voice emotion classifier.")
    ap.add_argument("--train-manifest", type=Path, required=True)
    ap.add_argument("--val-manifest", type=Path, required=True)
    ap.add_argument(
        "--backend",
        type=str,
        default="transformers",
        choices=["transformers", "torchaudio"],
    )
    ap.add_argument("--model", type=str, default="facebook/wav2vec2-base")
    ap.add_argument("--bundle", type=str, default="WAVLM_BASE_PLUS")
    ap.add_argument("--torch-checkpoint-dir", type=Path, default=Path("models/torchaudio_backbones"))
    ap.add_argument("--require-local-backbone", dest="require_local_backbone", action="store_true", default=True)
    ap.add_argument("--no-require-local-backbone", dest="require_local_backbone", action="store_false")
    ap.add_argument("--device", type=str, default="auto")
    ap.add_argument("--output-dir", type=Path, default=Path("models/voice_emotion_ssl"))
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--grad-accum", type=int, default=1)
    ap.add_argument("--learning-rate", type=float, default=1e-4)
    ap.add_argument("--warmup-ratio", type=float, default=0.1)
    ap.add_argument("--weight-decay", type=float, default=0.01)
    ap.add_argument("--lr-scheduler", type=str, default="linear")
    ap.add_argument("--num-workers", type=int, default=2)
    ap.add_argument("--save-steps", type=int, default=200)
    ap.add_argument("--eval-steps", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--freeze-feature-encoder", action="store_true", default=True)
    ap.add_argument("--no-freeze-feature-encoder", dest="freeze_feature_encoder", action="store_false")
    ap.add_argument("--freeze-epochs", type=float, default=1.0)
    ap.add_argument("--unfreeze-step", type=int, default=0)
    ap.add_argument("--use-class-weights", dest="use_class_weights", action="store_true", default=True)
    ap.add_argument("--no-class-weights", dest="use_class_weights", action="store_false")
    ap.add_argument("--balanced-sampler", dest="balanced_sampler", action="store_true", default=True)
    ap.add_argument("--no-balanced-sampler", dest="balanced_sampler", action="store_false")
    ap.add_argument("--gradient-checkpointing", action="store_true", default=False)
    ap.add_argument("--max-grad-norm", type=float, default=1.0)
    ap.add_argument("--log-steps", type=int, default=50)
    ap.add_argument("--classifier-dropout", type=float, default=0.1)
    ap.add_argument("--augment", dest="augment", action="store_true", default=True)
    ap.add_argument("--no-augment", dest="augment", action="store_false")
    ap.add_argument("--aug-prob", type=float, default=0.5)
    ap.add_argument("--aug-noise-std", type=float, default=0.003)
    ap.add_argument("--aug-gain-min", type=float, default=0.8)
    ap.add_argument("--aug-gain-max", type=float, default=1.25)
    ap.add_argument("--aug-time-shift-ms", type=int, default=50)
    ap.add_argument("--aug-time-mask-ms", type=int, default=0)
    ap.add_argument("--max-steps", type=int, default=0)
    ap.add_argument("--resume-from-checkpoint", type=str, default=None)
    return ap.parse_args()


def seed_everything(seed: int) -> None:
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    try:
        from transformers import set_seed

        set_seed(seed)
    except Exception:
        pass


def select_device(device: str) -> str:
    import torch

    if device != "auto":
        return device
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def train_torchaudio(args: argparse.Namespace) -> None:
    import torch
    from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
    from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler

    from app.models.voice.ssl_torchaudio import (
        EmotionTorchaudioClassifier,
        infer_feature_dim,
        load_pretrained_backbone,
        save_bundle_config,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    seed_everything(args.seed)

    train_df = load_manifest(args.train_manifest)
    val_df = load_manifest(args.val_manifest)
    label2id, id2label = build_label_maps(train_df)

    labels = train_df["label"].map(label2id).to_numpy()
    class_counts = np.bincount(labels, minlength=len(label2id)).astype(np.float64)
    class_counts[class_counts == 0] = 1.0
    majority = class_counts.max()
    baseline_acc = float(majority / class_counts.sum())
    print(
        "[voice-ssl] backend=torchaudio "
        f"samples={int(class_counts.sum())} classes={len(label2id)} "
        f"majority_baseline={baseline_acc:.3f}"
    )
    print("[voice-ssl] class_counts=" + ", ".join(str(int(v)) for v in class_counts))

    args.torch_checkpoint_dir.mkdir(parents=True, exist_ok=True)
    backbone, bundle_cfg = load_pretrained_backbone(
        args.bundle,
        model_dir=args.torch_checkpoint_dir,
        require_local=args.require_local_backbone,
    )
    sampling_rate = int(bundle_cfg.sample_rate)

    augmenter = None
    if args.augment:
        augmenter = WaveformAugmenter(
            AugmentConfig(
                enabled=True,
                prob=args.aug_prob,
                noise_std=args.aug_noise_std,
                gain_min=args.aug_gain_min,
                gain_max=args.aug_gain_max,
                time_shift_ms=args.aug_time_shift_ms,
                time_mask_ms=args.aug_time_mask_ms,
                sampling_rate=sampling_rate,
            ),
            seed=args.seed,
        )
        print(
            "[voice-ssl] augment=on "
            f"prob={args.aug_prob} noise_std={args.aug_noise_std} "
            f"gain=[{args.aug_gain_min},{args.aug_gain_max}] "
            f"time_shift_ms={args.aug_time_shift_ms} time_mask_ms={args.aug_time_mask_ms}"
        )

    class EmotionDataset(Dataset):
        def __init__(self, df):
            self.paths = df["path"].astype(str).tolist()
            self.labels = df["label"].map(label2id).astype(int).tolist()

        def __len__(self):
            return len(self.paths)

        def __getitem__(self, idx):
            audio = load_audio(self.paths[idx], sampling_rate)
            return audio, self.labels[idx]

    def collate(batch, aug: WaveformAugmenter | None):
        waves, targets = zip(*batch)
        if aug is not None:
            waves = [aug(w) for w in waves]
        lengths = torch.tensor([len(w) for w in waves], dtype=torch.long)
        tensors = [torch.tensor(w, dtype=torch.float32) for w in waves]
        padded = torch.nn.utils.rnn.pad_sequence(tensors, batch_first=True)
        return {
            "input_values": padded,
            "lengths": lengths,
            "labels": torch.tensor(targets, dtype=torch.long),
        }

    train_ds = EmotionDataset(train_df)
    val_ds = EmotionDataset(val_df)

    sample_weights = None
    if args.balanced_sampler:
        sample_weights = (1.0 / class_counts)[labels]

    pin_memory = False if select_device(args.device) == "mps" else True
    if args.balanced_sampler:
        sampler = WeightedRandomSampler(
            torch.as_tensor(sample_weights, dtype=torch.double),
            num_samples=len(sample_weights),
            replacement=True,
        )
        train_loader = DataLoader(
            train_ds,
            batch_size=args.batch_size,
            sampler=sampler,
            num_workers=args.num_workers,
            pin_memory=pin_memory,
            collate_fn=lambda b: collate(b, augmenter),
        )
    else:
        train_loader = DataLoader(
            train_ds,
            batch_size=args.batch_size,
            shuffle=True,
            num_workers=args.num_workers,
            pin_memory=pin_memory,
            collate_fn=lambda b: collate(b, augmenter),
        )

    val_loader = DataLoader(
        val_ds,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=pin_memory,
        collate_fn=lambda b: collate(b, None),
    )

    hidden_dim = infer_feature_dim(backbone, sampling_rate, device="cpu", model_type=bundle_cfg.model_type)
    model = EmotionTorchaudioClassifier(
        backbone,
        hidden_dim,
        len(label2id),
        dropout=args.classifier_dropout,
        model_type=bundle_cfg.model_type,
    )

    if args.freeze_feature_encoder and hasattr(model.backbone, "feature_extractor"):
        for param in model.backbone.feature_extractor.parameters():
            param.requires_grad = False
        print(
            "[voice-ssl] freeze_feature_encoder=on "
            f"freeze_epochs={args.freeze_epochs} unfreeze_step={args.unfreeze_step}"
        )

    device = select_device(args.device)
    model.to(device)

    class_weights = None
    if args.use_class_weights:
        weights = class_counts.sum() / (len(class_counts) * class_counts)
        class_weights = torch.tensor(weights, dtype=torch.float32, device=device)
    criterion = torch.nn.CrossEntropyLoss(weight=class_weights)

    def build_param_groups():
        decay = []
        no_decay = []
        for name, param in model.named_parameters():
            if not param.requires_grad:
                continue
            if param.ndim == 1 or name.endswith(".bias") or "norm" in name.lower():
                no_decay.append(param)
            else:
                decay.append(param)
        groups = []
        if decay:
            groups.append({"params": decay, "weight_decay": args.weight_decay})
        if no_decay:
            groups.append({"params": no_decay, "weight_decay": 0.0})
        return groups

    optimizer = torch.optim.AdamW(build_param_groups(), lr=args.learning_rate)
    total_steps = args.max_steps if args.max_steps > 0 else int(
        (len(train_loader) / max(1, args.grad_accum)) * args.epochs
    )
    warmup_steps = int(total_steps * args.warmup_ratio)

    def lr_lambda(step: int):
        if step < warmup_steps:
            return float(step) / max(1, warmup_steps)
        return max(0.0, float(total_steps - step) / max(1, total_steps - warmup_steps))

    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda=lr_lambda)

    run_meta = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "backend": "torchaudio",
        "bundle": args.bundle,
        "train_manifest": str(args.train_manifest),
        "val_manifest": str(args.val_manifest),
        "num_classes": len(label2id),
        "class_counts": {label: int(class_counts[idx]) for label, idx in label2id.items()},
        "majority_baseline_accuracy": baseline_acc,
        "args": vars(args),
    }
    (args.output_dir / "run_config.json").write_text(json.dumps(run_meta, indent=2))

    bundle_cfg.hidden_dim = hidden_dim
    bundle_cfg.num_labels = len(label2id)
    save_bundle_config(args.output_dir / "torchaudio_bundle.json", bundle_cfg)
    (args.output_dir / "label_map.json").write_text(
        json.dumps(
            {
                "label2id": label2id,
                "id2label": id2label,
                "backend": "torchaudio",
                "bundle": args.bundle,
            },
            indent=2,
        )
    )

    best_macro_f1 = -1.0
    global_step = 0
    unfroze = False

    def maybe_unfreeze(epoch_float: float):
        nonlocal unfroze
        if unfroze or not args.freeze_feature_encoder or not hasattr(model.backbone, "feature_extractor"):
            return
        if args.unfreeze_step > 0 and global_step < args.unfreeze_step:
            return
        if args.freeze_epochs > 0 and epoch_float < args.freeze_epochs:
            return
        for param in model.backbone.feature_extractor.parameters():
            param.requires_grad = True
        existing = {id(p) for group in optimizer.param_groups for p in group["params"]}
        new_params = [p for p in model.backbone.feature_extractor.parameters() if id(p) not in existing]
        if new_params:
            optimizer.add_param_group({"params": new_params, "weight_decay": args.weight_decay})
        unfroze = True
        print(f"[voice-ssl] unfreeze_feature_encoder step={global_step} epoch={epoch_float:.3f}")

    def evaluate(epoch_float: float):
        model.eval()
        all_preds = []
        all_labels = []
        total_loss = 0.0
        total = 0
        with torch.no_grad():
            for batch in val_loader:
                inputs = batch["input_values"].to(device)
                lengths = batch["lengths"].to(device)
                labels_batch = batch["labels"].to(device)
                logits = model(inputs, lengths)
                loss = criterion(logits, labels_batch)
                total_loss += loss.item() * labels_batch.size(0)
                total += labels_batch.size(0)
                preds = torch.argmax(logits, dim=-1)
                all_preds.extend(preds.cpu().numpy().tolist())
                all_labels.extend(labels_batch.cpu().numpy().tolist())
        eval_loss = total_loss / max(1, total)
        eval_accuracy = accuracy_score(all_labels, all_preds)
        eval_macro_f1 = f1_score(all_labels, all_preds, average="macro")
        eval_uar = balanced_accuracy_score(all_labels, all_preds)
        metrics = {
            "eval_loss": f"{eval_loss:.3f}",
            "eval_accuracy": f"{eval_accuracy:.3f}",
            "eval_macro_f1": f"{eval_macro_f1:.4f}",
            "eval_uar": f"{eval_uar:.3f}",
            "epoch": f"{epoch_float:.3f}",
        }
        print(metrics)
        return eval_macro_f1

    for epoch in range(args.epochs):
        model.train()
        for step, batch in enumerate(train_loader, start=1):
            epoch_float = epoch + step / max(1, len(train_loader))
            maybe_unfreeze(epoch_float)
            inputs = batch["input_values"].to(device)
            lengths = batch["lengths"].to(device)
            labels_batch = batch["labels"].to(device)
            logits = model(inputs, lengths)
            loss = criterion(logits, labels_batch)
            loss = loss / max(1, args.grad_accum)
            loss.backward()

            if step % args.grad_accum == 0:
                grad_norm = 0.0
                if args.max_grad_norm and args.max_grad_norm > 0:
                    grad_norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), args.max_grad_norm))
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad(set_to_none=True)
                global_step += 1

                if global_step % args.log_steps == 0:
                    print(
                        {
                            "loss": f"{loss.item():.3f}",
                            "grad_norm": f"{grad_norm:.4f}",
                            "learning_rate": f"{scheduler.get_last_lr()[0]:.3e}",
                            "epoch": f"{epoch_float:.3f}",
                        }
                    )

                if args.eval_steps > 0 and global_step % args.eval_steps == 0:
                    macro_f1 = evaluate(epoch_float)
                    if macro_f1 > best_macro_f1:
                        best_macro_f1 = macro_f1
                        torch.save(model.state_dict(), args.output_dir / "torchaudio_model.pt")

                if args.max_steps > 0 and global_step >= args.max_steps:
                    break
        if args.max_steps > 0 and global_step >= args.max_steps:
            break

    torch.save(model.state_dict(), args.output_dir / "torchaudio_model.pt")
    print(f"[voice-ssl] saved model to {args.output_dir}")


def main() -> None:
    args = parse_args()
    if args.backend == "torchaudio":
        train_torchaudio(args)
        return

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

    args.output_dir.mkdir(parents=True, exist_ok=True)
    seed_everything(args.seed)

    train_df = load_manifest(args.train_manifest)
    val_df = load_manifest(args.val_manifest)

    label2id, id2label = build_label_maps(train_df)

    labels = train_df["label"].map(label2id).to_numpy()
    class_counts = np.bincount(labels, minlength=len(label2id)).astype(np.float64)
    class_counts[class_counts == 0] = 1.0
    majority = class_counts.max()
    baseline_acc = float(majority / class_counts.sum())
    print(
        "[voice-ssl] train samples="
        f"{int(class_counts.sum())} classes={len(label2id)} "
        f"majority_baseline={baseline_acc:.3f}"
    )
    print("[voice-ssl] class_counts=" + ", ".join(str(int(v)) for v in class_counts))
    class_count_map = {label: int(class_counts[idx]) for label, idx in label2id.items()}
    run_meta = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "backend": "transformers",
        "model": args.model,
        "train_manifest": str(args.train_manifest),
        "val_manifest": str(args.val_manifest),
        "num_classes": len(label2id),
        "class_counts": class_count_map,
        "majority_baseline_accuracy": baseline_acc,
        "args": vars(args),
    }
    (args.output_dir / "run_config.json").write_text(json.dumps(run_meta, indent=2))

    feature_extractor = AutoFeatureExtractor.from_pretrained(args.model)
    sampling_rate = int(getattr(feature_extractor, "sampling_rate", 16000))
    augmenter = None
    if args.augment:
        augmenter = WaveformAugmenter(
            AugmentConfig(
                enabled=True,
                prob=args.aug_prob,
                noise_std=args.aug_noise_std,
                gain_min=args.aug_gain_min,
                gain_max=args.aug_gain_max,
                time_shift_ms=args.aug_time_shift_ms,
                time_mask_ms=args.aug_time_mask_ms,
                sampling_rate=sampling_rate,
            ),
            seed=args.seed,
        )
        print(
            "[voice-ssl] augment=on "
            f"prob={args.aug_prob} noise_std={args.aug_noise_std} "
            f"gain=[{args.aug_gain_min},{args.aug_gain_max}] "
            f"time_shift_ms={args.aug_time_shift_ms} time_mask_ms={args.aug_time_mask_ms}"
        )
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
        weights = class_counts.sum() / (len(class_counts) * class_counts)
        class_weights = torch.tensor(weights, dtype=torch.float32)

    sample_weights = None
    if args.balanced_sampler:
        sample_weights = (1.0 / class_counts)[labels]

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=-1)
        return {
            "accuracy": accuracy_score(labels, preds),
            "macro_f1": f1_score(labels, preds, average="macro"),
            "uar": balanced_accuracy_score(labels, preds),
        }

    class WeightedTrainer(Trainer):
        def __init__(
            self,
            *args,
            class_weights=None,
            sample_weights=None,
            train_collator=None,
            eval_collator=None,
            freeze_epochs=0.0,
            unfreeze_step=0,
            freeze_feature_encoder=False,
            **kwargs,
        ):
            super().__init__(*args, **kwargs)
            self.class_weights = class_weights
            self.sample_weights = sample_weights
            self.train_collator = train_collator
            self.eval_collator = eval_collator
            self.freeze_epochs = float(freeze_epochs or 0.0)
            self.unfreeze_step = int(unfreeze_step or 0)
            self.freeze_feature_encoder = bool(freeze_feature_encoder)
            self._unfroze = False

        def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
            labels = inputs.pop("labels")
            outputs = model(**inputs)
            logits = outputs.logits
            weights = self.class_weights.to(logits.device) if self.class_weights is not None else None
            loss_fn = torch.nn.CrossEntropyLoss(weight=weights)
            loss = loss_fn(logits, labels)
            return (loss, outputs) if return_outputs else loss

        def _add_unfrozen_params_to_optimizer(self):
            if self.optimizer is None:
                return
            existing = {id(p) for group in self.optimizer.param_groups for p in group["params"]}
            decay_names = set(self.get_decay_parameter_names(self.model))
            decay = []
            no_decay = []
            for name, param in self.model.named_parameters():
                if not param.requires_grad or id(param) in existing:
                    continue
                if name in decay_names:
                    decay.append(param)
                else:
                    no_decay.append(param)
            if decay:
                self.optimizer.add_param_group(
                    {
                        "params": decay,
                        "weight_decay": self.args.weight_decay,
                        "lr": self.args.learning_rate,
                    }
                )
            if no_decay:
                self.optimizer.add_param_group(
                    {"params": no_decay, "weight_decay": 0.0, "lr": self.args.learning_rate}
                )

        def _maybe_unfreeze(self):
            if self._unfroze or not self.freeze_feature_encoder:
                return
            should_unfreeze = False
            if self.unfreeze_step > 0 and self.state.global_step >= self.unfreeze_step:
                should_unfreeze = True
            if self.freeze_epochs > 0 and self.state.epoch is not None and self.state.epoch >= self.freeze_epochs:
                should_unfreeze = True
            if not should_unfreeze:
                return
            if hasattr(self.model, "unfreeze_feature_encoder"):
                self.model.unfreeze_feature_encoder()
            else:
                for param in self.model.parameters():
                    param.requires_grad = True
            self._add_unfrozen_params_to_optimizer()
            self._unfroze = True
            print(
                "[voice-ssl] unfreeze_feature_encoder "
                f"step={self.state.global_step} epoch={self.state.epoch}"
            )

        def training_step(self, model, inputs):
            self._maybe_unfreeze()
            return super().training_step(model, inputs)

        def get_train_dataloader(self):
            if self.train_dataset is None:
                raise ValueError("Trainer: training requires a train_dataset.")
            if self.sample_weights is None:
                return super().get_train_dataloader()
            from torch.utils.data import DataLoader, WeightedRandomSampler

            weights = torch.as_tensor(self.sample_weights, dtype=torch.double)
            sampler = WeightedRandomSampler(weights=weights, num_samples=len(weights), replacement=True)
            return DataLoader(
                self.train_dataset,
                batch_size=self.args.train_batch_size,
                sampler=sampler,
                collate_fn=self.train_collator or self.data_collator,
                drop_last=self.args.dataloader_drop_last,
                num_workers=self.args.dataloader_num_workers,
                pin_memory=self.args.dataloader_pin_memory,
                persistent_workers=getattr(self.args, "dataloader_persistent_workers", False),
            )

        def get_eval_dataloader(self, eval_dataset=None):
            eval_dataset = eval_dataset if eval_dataset is not None else self.eval_dataset
            if eval_dataset is None:
                raise ValueError("Trainer: evaluation requires an eval_dataset.")
            from torch.utils.data import DataLoader

            return DataLoader(
                eval_dataset,
                sampler=self.get_eval_sampler(eval_dataset),
                batch_size=self.args.eval_batch_size,
                collate_fn=self.eval_collator or self.data_collator,
                drop_last=self.args.dataloader_drop_last,
                num_workers=self.args.dataloader_num_workers,
                pin_memory=self.args.dataloader_pin_memory,
                persistent_workers=getattr(self.args, "dataloader_persistent_workers", False),
            )

    training_kwargs = {
        "output_dir": str(args.output_dir),
        "per_device_train_batch_size": args.batch_size,
        "per_device_eval_batch_size": args.batch_size,
        "gradient_accumulation_steps": max(1, int(args.grad_accum)),
        "learning_rate": args.learning_rate,
        "warmup_ratio": args.warmup_ratio,
        "weight_decay": args.weight_decay,
        "lr_scheduler_type": args.lr_scheduler,
        "num_train_epochs": args.epochs,
        "max_steps": args.max_steps if args.max_steps > 0 else -1,
        "save_steps": args.save_steps,
        "eval_steps": args.eval_steps,
        "logging_steps": args.log_steps,
        "max_grad_norm": args.max_grad_norm,
        "save_total_limit": 2,
        "load_best_model_at_end": True,
        "metric_for_best_model": "macro_f1",
        "report_to": "none",
        "fp16": torch.cuda.is_available(),
        "dataloader_num_workers": args.num_workers,
        "seed": args.seed,
    }
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        training_kwargs["dataloader_pin_memory"] = False

    if args.gradient_checkpointing:
        training_kwargs["gradient_checkpointing"] = True

    import inspect

    sig = inspect.signature(TrainingArguments.__init__)
    if "evaluation_strategy" in sig.parameters:
        training_kwargs["evaluation_strategy"] = "steps"
    elif "eval_strategy" in sig.parameters:
        training_kwargs["eval_strategy"] = "steps"

    filtered_kwargs = {k: v for k, v in training_kwargs.items() if k in sig.parameters}
    training_args = TrainingArguments(**filtered_kwargs)

    train_collator = AugmentingAudioDataCollator(feature_extractor, augmenter)
    eval_collator = AudioDataCollator(feature_extractor)

    if args.freeze_feature_encoder:
        print(
            "[voice-ssl] freeze_feature_encoder=on "
            f"freeze_epochs={args.freeze_epochs} unfreeze_step={args.unfreeze_step}"
        )

    trainer_kwargs = {
        "model": model,
        "args": training_args,
        "train_dataset": train_ds,
        "eval_dataset": val_ds,
        "data_collator": train_collator,
        "compute_metrics": compute_metrics,
        "class_weights": class_weights,
        "sample_weights": sample_weights,
        "train_collator": train_collator,
        "eval_collator": eval_collator,
        "freeze_epochs": args.freeze_epochs,
        "unfreeze_step": args.unfreeze_step,
        "freeze_feature_encoder": args.freeze_feature_encoder,
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
        "backend": "transformers",
    }
    (args.output_dir / "label_map.json").write_text(json.dumps(meta, indent=2))
    print(f"[voice-ssl] saved model to {args.output_dir}")


if __name__ == "__main__":
    main()
