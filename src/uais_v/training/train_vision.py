"""Train a ResNet-based vision classifier for deepfake/forgery detection.

Expects ImageFolder layout under data_dir with train/ and val/ subdirectories.
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
    epochs: int = 3
    lr: float = 1e-3
    num_workers: int = 2


def build_dataloaders(data_dir: Path, batch_size: int, num_workers: int) -> Tuple[DataLoader, DataLoader]:
    transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    train_ds = ImageFolder(data_dir / "train", transform=transform)
    val_ds = ImageFolder(data_dir / "val", transform=transform)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    return train_loader, val_loader


def train_resnet_classifier(
    data_dir: Path,
    vision_cfg: VisionConfig,
    train_cfg: VisionTrainConfig,
    save_dir: Path | None = None,
) -> Tuple[nn.Module, dict, Path | None]:
    set_global_seed(42)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_loader, val_loader = build_dataloaders(data_dir, train_cfg.batch_size, train_cfg.num_workers)

    model = build_resnet_classifier(vision_cfg).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=train_cfg.lr)

    model.train()
    for epoch in range(train_cfg.epochs):
        epoch_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * len(labels)
        epoch_loss /= len(train_loader.dataset)
        print(f"[Vision] epoch {epoch+1}/{train_cfg.epochs} loss {epoch_loss:.4f}")

    # simple eval
    model.eval()
    all_probs = []
    all_labels = []
    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(device)
            logits = model(images)
            probs = torch.softmax(logits, dim=1)[:, 1].cpu().numpy()
            all_probs.append(probs)
            all_labels.append(labels.numpy())
    probs = np.concatenate(all_probs) if all_probs else np.array([])
    labels = np.concatenate(all_labels) if all_labels else np.array([])
    metrics = classification_metrics(labels, probs, threshold=0.5) if len(labels) else {}

    out_dir = None
    if save_dir is not None:
        out_dir = Path(save_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        torch.save(model.state_dict(), out_dir / "model.pt")
        print(f"Saved vision model to {out_dir}")

    return model, metrics, out_dir


__all__ = ["train_resnet_classifier", "VisionTrainConfig", "build_dataloaders"]
