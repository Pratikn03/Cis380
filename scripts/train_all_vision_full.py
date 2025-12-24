#!/usr/bin/env python3
"""
Full vision training (deepfake + real/fake).

Trains:
- Deepfake detector on Celeb_V2 using MobileNetV2
- Real/Fake image classifier on raw vision dataset using EfficientNet-B0

Defaults assume the dataset layout already exists locally:
- Celeb_V2: data/Celeb_V2/{Train,Val,Test}/{real,fake}/*.jpg
- Raw vision: data/raw/vision/{train_real,train_fake}/**/*.(jpg|png)

Outputs:
- models/vision/deepfake_full.pt
- models/vision/realfake_full.pt
"""

from __future__ import annotations

import argparse
import random
from collections import Counter
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
REPO_ROOT = Path(__file__).resolve().parents[1]


def _resolve_device(requested: str) -> torch.device:
    req = (requested or "auto").strip().lower()
    if req == "auto":
        if torch.backends.mps.is_available():
            return torch.device("mps")
        if torch.cuda.is_available():
            return torch.device("cuda")
        return torch.device("cpu")
    if req in {"cpu", "cuda", "mps"}:
        if req == "cuda" and not torch.cuda.is_available():
            raise SystemExit("Requested device=cuda but CUDA is not available.")
        if req == "mps" and not torch.backends.mps.is_available():
            raise SystemExit("Requested device=mps but MPS is not available.")
        return torch.device(req)
    raise SystemExit(f"Unsupported --device={requested!r}. Use auto|cpu|cuda|mps.")


def _set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _print_header(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def _cap_list(items: list[str], limit: int) -> list[str]:
    if limit <= 0:
        return items
    return items[:limit]


class ImageDataset(Dataset):
    def __init__(self, image_paths: list[str], labels: list[int], transform):
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, idx: int):
        try:
            img = Image.open(self.image_paths[idx]).convert("RGB")
        except Exception:
            img = Image.new("RGB", (224, 224), "black")
        return self.transform(img), int(self.labels[idx])


def _collect_images_flat(root: Path) -> list[str]:
    if not root.exists():
        return []
    images: list[str] = []
    for p in root.iterdir():
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            images.append(str(p))
    return images


def _collect_images_recursive(root: Path) -> list[str]:
    if not root.exists():
        return []
    images: list[str] = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            images.append(str(p))
    return images


def train_deepfake_full(
    *,
    device: torch.device,
    out_dir: Path,
    celeb_root: Path,
    epochs: int,
    batch_size: int,
    num_workers: int,
    max_train: int,
    max_val: int,
    pretrained: bool,
) -> float | None:
    _print_header("🎭 DEEPFAKE DETECTOR - FULL CELEB_V2 DATASET")

    train_images: list[str] = []
    train_labels: list[int] = []
    val_images: list[str] = []
    val_labels: list[int] = []

    celeb_train = celeb_root / "Train"
    celeb_val = celeb_root / "Val"
    celeb_test = celeb_root / "Test"

    for label, folder in [(0, "real"), (1, "fake")]:
        for split_dir in [celeb_train, celeb_val]:
            imgs = _collect_images_flat(split_dir / folder)
            train_images.extend(imgs)
            train_labels.extend([label] * len(imgs))

    for label, folder in [(0, "real"), (1, "fake")]:
        imgs = _collect_images_flat(celeb_test / folder)
        val_images.extend(imgs)
        val_labels.extend([label] * len(imgs))

    train_images = _cap_list(train_images, max_train)
    train_labels = train_labels[: len(train_images)]
    val_images = _cap_list(val_images, max_val)
    val_labels = val_labels[: len(val_images)]

    print(f"📊 Training samples: {len(train_images):,}")
    print(f"📊 Validation samples: {len(val_images):,}")
    print(f"📊 Class distribution: {Counter(train_labels)}")

    if not train_images:
        print("❌ No Celeb_V2 training data found.")
        print(f"   Expected: {celeb_root}/{{Train,Val}}/{{real,fake}}/*.jpg")
        return None
    if not val_images:
        print("❌ No Celeb_V2 validation data found.")
        print(f"   Expected: {celeb_root}/Test/{{real,fake}}/*.jpg")
        return None

    train_transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(0.5),
            transforms.RandomRotation(10),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )
    val_transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )

    train_dataset = ImageDataset(train_images, train_labels, train_transform)
    val_dataset = ImageDataset(val_images, val_labels, val_transform)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)

    weights = models.MobileNet_V2_Weights.IMAGENET1K_V1 if pretrained else None
    model = models.mobilenet_v2(weights=weights)
    model.classifier[1] = nn.Linear(model.last_channel, 2)
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)
    scheduler = optim.lr_scheduler.OneCycleLR(
        optimizer, max_lr=0.003, steps_per_epoch=len(train_loader), epochs=epochs
    )

    best_acc = 0.0
    best_path = out_dir / "deepfake_full.pt"

    for epoch in range(epochs):
        model.train()
        correct = 0
        total = 0

        for batch_idx, (images, labels) in enumerate(train_loader):
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            scheduler.step()

            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

            if batch_idx % 100 == 0:
                acc = 100.0 * correct / max(1, total)
                print(
                    f"  Epoch {epoch+1}/{epochs} | Batch {batch_idx}/{len(train_loader)} | "
                    f"Loss: {loss.item():.4f} | Acc: {acc:.2f}%"
                )

        model.eval()
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(device)
                labels = labels.to(device)
                outputs = model(images)
                _, predicted = outputs.max(1)
                val_total += labels.size(0)
                val_correct += predicted.eq(labels).sum().item()

        val_acc = 100.0 * val_correct / max(1, val_total)
        train_acc = 100.0 * correct / max(1, total)
        print(f"📈 Epoch {epoch+1} - Train Acc: {train_acc:.2f}% | Val Acc: {val_acc:.2f}%")

        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), best_path)

    print(f"\n✅ DEEPFAKE BEST ACCURACY: {best_acc:.2f}%")
    print(f"📁 Saved: {best_path}")
    return best_acc


def train_realfake_full(
    *,
    device: torch.device,
    out_dir: Path,
    raw_vision_root: Path,
    epochs: int,
    batch_size: int,
    num_workers: int,
    val_split: float,
    max_train: int,
    max_val: int,
    pretrained: bool,
) -> float | None:
    _print_header("🖼️ REAL/FAKE CLASSIFIER - FULL RAW VISION DATASET")

    real_dir = raw_vision_root / "train_real"
    fake_dir = raw_vision_root / "train_fake"

    real_images = _collect_images_recursive(real_dir)
    fake_images = _collect_images_recursive(fake_dir)

    all_images = real_images + fake_images
    all_labels = [0] * len(real_images) + [1] * len(fake_images)

    print(f"📊 Total samples: {len(all_images):,}")
    print(f"📊 Class distribution: {Counter(all_labels)}")

    if not all_images:
        print("❌ No raw vision data found.")
        print(f"   Expected: {raw_vision_root}/train_real/**/*.(jpg|png)")
        print(f"   Expected: {raw_vision_root}/train_fake/**/*.(jpg|png)")
        return None

    from sklearn.model_selection import train_test_split

    train_imgs, val_imgs, train_lbls, val_lbls = train_test_split(
        all_images, all_labels, test_size=val_split, random_state=42, stratify=all_labels
    )

    train_imgs = _cap_list(train_imgs, max_train)
    train_lbls = train_lbls[: len(train_imgs)]
    val_imgs = _cap_list(val_imgs, max_val)
    val_lbls = val_lbls[: len(val_imgs)]

    print(f"📊 Training: {len(train_imgs):,} | Validation: {len(val_imgs):,}")

    train_transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(0.5),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )
    val_transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )

    train_dataset = ImageDataset(train_imgs, train_lbls, train_transform)
    val_dataset = ImageDataset(val_imgs, val_lbls, val_transform)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)

    weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1 if pretrained else None
    model = models.efficientnet_b0(weights=weights)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, 2)
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)
    scheduler = optim.lr_scheduler.OneCycleLR(
        optimizer, max_lr=0.003, steps_per_epoch=len(train_loader), epochs=epochs
    )

    best_acc = 0.0
    best_path = out_dir / "realfake_full.pt"

    for epoch in range(epochs):
        model.train()
        correct = 0
        total = 0

        for batch_idx, (images, labels) in enumerate(train_loader):
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            scheduler.step()

            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

            if batch_idx % 100 == 0:
                acc = 100.0 * correct / max(1, total)
                print(
                    f"  Epoch {epoch+1}/{epochs} | Batch {batch_idx}/{len(train_loader)} | "
                    f"Loss: {loss.item():.4f} | Acc: {acc:.2f}%"
                )

        model.eval()
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(device)
                labels = labels.to(device)
                outputs = model(images)
                _, predicted = outputs.max(1)
                val_total += labels.size(0)
                val_correct += predicted.eq(labels).sum().item()

        val_acc = 100.0 * val_correct / max(1, val_total)
        train_acc = 100.0 * correct / max(1, total)
        print(f"📈 Epoch {epoch+1} - Train Acc: {train_acc:.2f}% | Val Acc: {val_acc:.2f}%")

        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), best_path)

    print(f"\n✅ REAL/FAKE BEST ACCURACY: {best_acc:.2f}%")
    print(f"📁 Saved: {best_path}")
    return best_acc


def main() -> int:
    parser = argparse.ArgumentParser(description="Train full vision models (deepfake + real/fake).")
    parser.add_argument("--device", default="auto", help="auto|cpu|cuda|mps")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--epochs", type=int, default=3, help="Epochs per model.")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size.")
    parser.add_argument("--num-workers", type=int, default=0, help="DataLoader workers.")
    parser.add_argument("--val-split", type=float, default=0.15, help="Validation split for real/fake dataset.")
    parser.add_argument("--max-train", type=int, default=0, help="Cap training samples (0 = no cap).")
    parser.add_argument("--max-val", type=int, default=0, help="Cap validation samples (0 = no cap).")
    parser.add_argument("--no-pretrained", action="store_true", help="Disable ImageNet pretrained weights.")

    parser.add_argument(
        "--out-dir",
        default=str(REPO_ROOT / "models" / "vision"),
        help="Where to write model weights (default: models/vision).",
    )
    parser.add_argument(
        "--celeb-root",
        default=str(REPO_ROOT / "data" / "Celeb_V2"),
        help="Celeb_V2 root containing Train/Val/Test (default: data/Celeb_V2).",
    )
    parser.add_argument(
        "--raw-vision-root",
        default=str(REPO_ROOT / "data" / "raw" / "vision"),
        help="Raw vision root containing train_real/ and train_fake/ (default: data/raw/vision).",
    )
    parser.add_argument("--deepfake", action="store_true", help="Train deepfake model (Celeb_V2).")
    parser.add_argument("--realfake", action="store_true", help="Train real/fake model (raw vision).")
    args = parser.parse_args()

    if args.epochs <= 0:
        raise SystemExit("--epochs must be >= 1")
    if args.batch_size <= 0:
        raise SystemExit("--batch-size must be >= 1")
    if args.num_workers < 0:
        raise SystemExit("--num-workers must be >= 0")
    if not (0.0 < float(args.val_split) < 1.0):
        raise SystemExit("--val-split must be between 0 and 1")

    device = _resolve_device(args.device)
    _set_seed(int(args.seed))

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    celeb_root = Path(args.celeb_root).expanduser().resolve()
    raw_vision_root = Path(args.raw_vision_root).expanduser().resolve()
    pretrained = not bool(args.no_pretrained)

    selected = {k for k, v in {"deepfake": args.deepfake, "realfake": args.realfake}.items() if v}
    if not selected:
        selected = {"deepfake", "realfake"}

    print(f"🚀 FULL VISION TRAINING - Device: {device}")
    print(f"📁 Output dir: {out_dir}")
    print(f"🔁 Epochs: {args.epochs} | Batch size: {args.batch_size} | Workers: {args.num_workers}")
    print("=" * 60)

    results: dict[str, float] = {}

    if "deepfake" in selected:
        acc = train_deepfake_full(
            device=device,
            out_dir=out_dir,
            celeb_root=celeb_root,
            epochs=int(args.epochs),
            batch_size=int(args.batch_size),
            num_workers=int(args.num_workers),
            max_train=int(args.max_train),
            max_val=int(args.max_val),
            pretrained=pretrained,
        )
        if acc is not None:
            results["deepfake"] = float(acc)

    if "realfake" in selected:
        acc = train_realfake_full(
            device=device,
            out_dir=out_dir,
            raw_vision_root=raw_vision_root,
            epochs=int(args.epochs),
            batch_size=int(args.batch_size),
            num_workers=int(args.num_workers),
            val_split=float(args.val_split),
            max_train=int(args.max_train),
            max_val=int(args.max_val),
            pretrained=pretrained,
        )
        if acc is not None:
            results["realfake"] = float(acc)

    _print_header("🎯 FULL VISION TRAINING COMPLETE")
    if not results:
        return 1
    for name, acc in results.items():
        status = "✅" if acc >= 95 else "⚠️"
        print(f"{status} {name}: {acc:.2f}%")
    avg = sum(results.values()) / len(results)
    print(f"\n📊 AVERAGE VISION ACCURACY: {avg:.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
