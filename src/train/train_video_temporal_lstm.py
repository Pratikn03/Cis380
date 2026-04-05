"""Train the TemporalDeepfakeLSTM model for /api/vision/video_temporal."""

from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader, Subset

from app.models.vision.temporal.dataset import VideoClipDataset
from app.models.vision.temporal.model import TemporalDeepfakeLSTM


def _resolve_device(requested: str | None) -> str:
    req = (requested or "").strip().lower()
    if not req or req == "auto":
        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"
    return req


def _split_indices(n: int, seed: int, val_ratio: float) -> tuple[list[int], list[int]]:
    idx = list(range(n))
    random.Random(seed).shuffle(idx)
    n_val = max(1, int(n * val_ratio))
    return idx[n_val:], idx[:n_val]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Train TemporalDeepfakeLSTM (video temporal model)."
    )
    parser.add_argument("--data-root", type=Path, default=Path("data/raw/vision/video"))
    parser.add_argument("--clip-len", type=int, default=16)
    parser.add_argument("--size", type=int, default=224)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--max-per-class", type=int, default=200)
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--device",
        type=str,
        default=os.getenv("Sentifargo_VISION_DEVICE", "auto"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("artifacts/vision_temporal/temporal_lstm.pt"),
    )
    args = parser.parse_args()

    dataset = VideoClipDataset(
        str(args.data_root), clip_len=int(args.clip_len), size=int(args.size)
    )
    if len(dataset) == 0:
        raise SystemExit(f"No videos found under {args.data_root}/real or {args.data_root}/fake")

    # Optional class balancing via max-per-class
    if args.max_per_class > 0:
        real_idx = [i for i, (_, y) in enumerate(dataset.items) if y == 0][: args.max_per_class]
        fake_idx = [i for i, (_, y) in enumerate(dataset.items) if y == 1][: args.max_per_class]
        keep = real_idx + fake_idx
        dataset = Subset(dataset, keep)

    train_idx, val_idx = _split_indices(
        len(dataset), seed=int(args.seed), val_ratio=float(args.val_ratio)
    )
    train_ds = Subset(dataset, train_idx)
    val_ds = Subset(dataset, val_idx)

    device = torch.device(_resolve_device(args.device))
    model = TemporalDeepfakeLSTM(
        hidden=256, backbone="mobilenet_v3_small", freeze_backbone=True
    ).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(args.lr))
    criterion = nn.BCEWithLogitsLoss()

    train_loader = DataLoader(
        train_ds, batch_size=int(args.batch_size), shuffle=True, num_workers=0
    )
    val_loader = DataLoader(val_ds, batch_size=int(args.batch_size), shuffle=False, num_workers=0)

    metrics = {
        "epochs": int(args.epochs),
        "train_samples": len(train_ds),
        "val_samples": len(val_ds),
    }

    for epoch in range(int(args.epochs)):
        model.train()
        running = 0.0
        for clips, labels in train_loader:
            clips = clips.to(device)
            labels = labels.to(device)
            optimizer.zero_grad()
            logits = model(clips)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            running += float(loss.item())

        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for clips, labels in val_loader:
                clips = clips.to(device)
                labels = labels.to(device)
                logits = model(clips)
                preds = (torch.sigmoid(logits) >= 0.5).float()
                correct += int((preds == labels).sum().item())
                total += int(labels.numel())

        metrics[f"epoch_{epoch+1}"] = {
            "loss": round(running / max(1, len(train_loader)), 6),
            "val_accuracy": round(correct / max(1, total), 6),
        }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "state_dict": model.state_dict(),
            "clip_len": int(args.clip_len),
            "size": int(args.size),
            "metrics": metrics,
        },
        args.out,
    )

    out_metrics = Path("experiments/vision/temporal_lstm/metrics.json")
    out_metrics.parent.mkdir(parents=True, exist_ok=True)
    out_metrics.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"[temporal-lstm] saved: {args.out}")
    print(f"[temporal-lstm] wrote: {out_metrics}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
