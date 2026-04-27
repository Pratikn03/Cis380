"""Train a ResNet-based vision classifier.

Supports two common dataset layouts:

1) Standard ImageFolder with explicit splits:

    <data_dir>/train/<class>/*.jpg
    <data_dir>/val/<class>/*.jpg

2) Kaggle Intel Image Classification (scene dataset) layout:

    <data_dir>/seg_train/seg_train/<class>/*.jpg
    <data_dir>/seg_test/seg_test/<class>/*.jpg

The trainer will auto-detect option (2) and map it to train/val.

Optionally saves the trained model to disk.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import transforms
from torchvision.datasets import ImageFolder

from uais_v.models.vision_resnet import VisionConfig, build_resnet_classifier
from uais_v.utils.seed import set_global_seed
from uais_v.evaluation.metrics import classification_metrics


@dataclass
class VisionTrainConfig:
    batch_size: int = 16
    epochs: int = 50
    lr: float = 1e-3
    num_workers: int = 2
    max_batches_per_epoch: int | None = None


def build_dataloaders(
    data_dir: Path, batch_size: int, num_workers: int
) -> Tuple[DataLoader, DataLoader]:
    transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    train_root, val_root = resolve_imagefolder_splits(data_dir)
    train_ds = ImageFolder(train_root, transform=transform)
    val_ds = ImageFolder(val_root, transform=transform)
    train_loader = DataLoader(
        train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers
    )
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    return train_loader, val_loader


def resolve_imagefolder_splits(data_dir: Path) -> Tuple[Path, Path]:
    """Resolve train/val roots given a dataset directory.

    Accepted:
    - data_dir/train and data_dir/val
    - data_dir/seg_train/seg_train and data_dir/seg_test/seg_test (Intel scenes dataset)
    """
    data_dir = Path(data_dir)

    # Standard expected layout
    train_std = data_dir / "train"
    val_std = data_dir / "val"
    if train_std.exists() and val_std.exists():
        return train_std, val_std

    # Intel scene dataset
    train_intel = data_dir / "seg_train" / "seg_train"
    val_intel = data_dir / "seg_test" / "seg_test"
    if train_intel.exists() and val_intel.exists():
        return train_intel, val_intel

    raise FileNotFoundError(
        "Could not find a supported ImageFolder split layout under "
        f"{data_dir}. Expected either train/val or Intel seg_train/seg_test."
    )


def train_resnet_classifier(
    data_dir: Path,
    vision_cfg: VisionConfig,
    train_cfg: VisionTrainConfig,
    save_dir: Path | None = None,
) -> Tuple[nn.Module, dict, Path | None]:
    set_global_seed(42)
    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")
    train_loader, val_loader = build_dataloaders(
        data_dir, train_cfg.batch_size, train_cfg.num_workers
    )

    # Determine number of classes from the dataset itself (supports multi-class scenes)
    _, val_loader = build_dataloaders(data_dir, train_cfg.batch_size, train_cfg.num_workers)
    num_classes = len(getattr(val_loader.dataset, "classes", []))
    if not num_classes:
        raise ValueError("Could not infer number of classes from ImageFolder dataset.")

    # Build model and ensure head matches class count.
    model = build_resnet_classifier(vision_cfg).to(device)
    if (
        hasattr(model, "fc")
        and isinstance(model.fc, nn.Linear)
        and model.fc.out_features != num_classes
    ):
        model.fc = nn.Linear(model.fc.in_features, num_classes).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=train_cfg.lr)

    model.train()
    for epoch in range(train_cfg.epochs):
        epoch_loss = 0.0
        seen = 0
        for step, (images, labels) in enumerate(train_loader, start=1):
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * len(labels)
            seen += len(labels)
            if (
                train_cfg.max_batches_per_epoch is not None
                and step >= train_cfg.max_batches_per_epoch
            ):
                break
        # ImageFolder exposes `samples`; prefer that for a type-checker-friendly length.
        epoch_loss /= max(seen, 1)
        print(f"[Vision] epoch {epoch+1}/{train_cfg.epochs} loss {epoch_loss:.4f}")

    # simple eval
    model.eval()
    all_probs = []
    all_labels = []
    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(device)
            logits = model(images)
            probs = torch.softmax(logits, dim=1).cpu().numpy()
            all_probs.append(probs)
            all_labels.append(labels.numpy())

    probs = np.concatenate(all_probs) if all_probs else np.array([])
    labels = np.concatenate(all_labels) if all_labels else np.array([])

    # The repo's classification_metrics is primarily for binary probabilities. For multi-class
    # we compute a lightweight accuracy and still surface binary metrics when applicable.
    metrics: dict = {}
    if len(labels):
        if probs.ndim == 2 and probs.shape[1] > 2:
            preds = probs.argmax(axis=1)
            metrics = {
                "accuracy": float((preds == labels).mean()),
                "num_classes": int(probs.shape[1]),
            }
        else:
            # Binary case: take prob(class=1)
            p1 = probs[:, 1] if probs.ndim == 2 and probs.shape[1] >= 2 else probs
            metrics = classification_metrics(labels, p1, threshold=0.5)

    out_dir = None
    if save_dir is not None:
        out_dir = Path(save_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        torch.save(model.state_dict(), out_dir / "model.pt")
        print(f"Saved vision model to {out_dir}")

    return model, metrics, out_dir


__all__ = ["train_resnet_classifier", "VisionTrainConfig", "build_dataloaders"]
