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
import multiprocessing as mp
import random
import time
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


def _log(message: str) -> None:
    print(message, flush=True)


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
    _log("\n" + "=" * 60)
    _log(title)
    _log("=" * 60)


def _cap_pairs(
    image_paths: list[str], labels: list[int], *, limit: int, seed: int
) -> tuple[list[str], list[int]]:
    if limit <= 0 or limit >= len(image_paths):
        return image_paths, labels
    idx = list(range(len(image_paths)))
    # Try to preserve class mix when downsampling.
    try:
        from sklearn.model_selection import train_test_split

        keep_idx, _ = train_test_split(
            idx,
            train_size=int(limit),
            random_state=int(seed),
            stratify=labels,
        )
    except Exception:
        rng = random.Random(int(seed))
        keep_idx = idx
        rng.shuffle(keep_idx)
        keep_idx = keep_idx[: int(limit)]
    keep_set = set(int(i) for i in keep_idx)
    out_paths = [p for i, p in enumerate(image_paths) if i in keep_set]
    out_labels = [int(y) for i, y in enumerate(labels) if i in keep_set]
    return out_paths, out_labels


def _probe_image_worker(path: str) -> None:
    try:
        with open(path, "rb") as handle:
            _ = handle.read(32)
        with Image.open(path) as img:
            img.verify()
    except Exception:
        raise SystemExit(1)
    raise SystemExit(0)


def _is_readable_with_timeout(path: str, timeout_sec: float) -> bool:
    if timeout_sec <= 0:
        return True
    ctx = mp.get_context("spawn")
    proc = ctx.Process(target=_probe_image_worker, args=(path,))
    proc.start()
    proc.join(timeout_sec)
    if proc.is_alive():
        proc.terminate()
        proc.join()
        return False
    return proc.exitcode == 0


def _filter_readable_pairs(
    image_paths: list[str],
    labels: list[int],
    *,
    timeout_sec: float,
    stage: str,
) -> tuple[list[str], list[int]]:
    if timeout_sec <= 0:
        return image_paths, labels
    out_paths: list[str] = []
    out_labels: list[int] = []
    dropped = 0
    total = len(image_paths)
    for i, (path, label) in enumerate(zip(image_paths, labels), start=1):
        if _is_readable_with_timeout(path, timeout_sec):
            out_paths.append(path)
            out_labels.append(int(label))
        else:
            dropped += 1
        if i % 50 == 0 or i == total:
            _log(
                f"[vision-full] {stage} probe {i}/{total} "
                f"(kept={len(out_paths)} dropped={dropped})"
            )
    return out_paths, out_labels


class ImageDataset(Dataset):
    def __init__(self, image_paths: list[str], labels: list[int], transform, image_size: int):
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform
        self.image_size = int(image_size)

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, idx: int):
        try:
            img = Image.open(self.image_paths[idx]).convert("RGB")
        except Exception:
            img = Image.new("RGB", (self.image_size, self.image_size), "black")
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
    seed: int,
    epochs: int,
    batch_size: int,
    num_workers: int,
    image_size: int,
    max_train: int,
    max_val: int,
    probe_timeout_sec: float,
    progress_every: int,
    max_seconds_per_model: int,
    freeze_backbone: bool,
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

    train_images, train_labels = _cap_pairs(
        train_images, train_labels, limit=int(max_train), seed=int(seed)
    )
    val_images, val_labels = _cap_pairs(
        val_images, val_labels, limit=int(max_val), seed=int(seed) + 1
    )
    train_images, train_labels = _filter_readable_pairs(
        train_images,
        train_labels,
        timeout_sec=float(probe_timeout_sec),
        stage="deepfake-train",
    )
    val_images, val_labels = _filter_readable_pairs(
        val_images,
        val_labels,
        timeout_sec=float(probe_timeout_sec),
        stage="deepfake-val",
    )

    _log(f"📊 Training samples: {len(train_images):,}")
    _log(f"📊 Validation samples: {len(val_images):,}")
    _log(f"📊 Class distribution: {Counter(train_labels)}")

    if not train_images:
        _log("❌ No Celeb_V2 training data found.")
        _log(f"   Expected: {celeb_root}/{{Train,Val}}/{{real,fake}}/*.jpg")
        return None
    if not val_images:
        _log("❌ No Celeb_V2 validation data found.")
        _log(f"   Expected: {celeb_root}/Test/{{real,fake}}/*.jpg")
        return None

    train_transform = transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.RandomHorizontalFlip(0.5),
            transforms.RandomRotation(10),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )
    val_transform = transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )

    train_dataset = ImageDataset(train_images, train_labels, train_transform, image_size)
    val_dataset = ImageDataset(val_images, val_labels, val_transform, image_size)

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=False,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=False,
    )

    weights = models.MobileNet_V2_Weights.IMAGENET1K_V1 if pretrained else None
    try:
        model = models.mobilenet_v2(weights=weights)
    except Exception as exc:
        if not pretrained:
            raise
        _log(
            "⚠️  Could not load pretrained MobileNetV2 weights; "
            f"falling back to random init. ({exc})"
        )
        model = models.mobilenet_v2(weights=None)
    model.classifier[1] = nn.Linear(model.last_channel, 2)
    if freeze_backbone:
        for p in model.features.parameters():
            p.requires_grad = False
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    trainable = [p for p in model.parameters() if p.requires_grad]
    optimizer = optim.AdamW(trainable, lr=0.001, weight_decay=0.01)
    scheduler = optim.lr_scheduler.OneCycleLR(
        optimizer, max_lr=0.003, steps_per_epoch=len(train_loader), epochs=epochs
    )

    best_acc = -1.0
    best_path = out_dir / "deepfake_full.pt"
    run_start = time.monotonic()

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

            if batch_idx % max(1, int(progress_every)) == 0 or batch_idx + 1 == len(train_loader):
                acc = 100.0 * correct / max(1, total)
                _log(
                    f"  Epoch {epoch+1}/{epochs} | Batch {batch_idx}/{len(train_loader)} | "
                    f"Loss: {loss.item():.4f} | Acc: {acc:.2f}%"
                )
            if int(max_seconds_per_model) > 0 and (time.monotonic() - run_start) > int(
                max_seconds_per_model
            ):
                _log(
                    f"⏱️  Reached --max-seconds-per-model={max_seconds_per_model}; "
                    "stopping deepfake training early."
                )
                break

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
        _log(f"📈 Epoch {epoch+1} - Train Acc: {train_acc:.2f}% | Val Acc: {val_acc:.2f}%")

        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), best_path)
        if int(max_seconds_per_model) > 0 and (time.monotonic() - run_start) > int(
            max_seconds_per_model
        ):
            break

    _log(f"\n✅ DEEPFAKE BEST ACCURACY: {best_acc:.2f}%")
    _log(f"📁 Saved: {best_path}")
    return best_acc


def train_realfake_full(
    *,
    device: torch.device,
    out_dir: Path,
    raw_vision_root: Path,
    seed: int,
    epochs: int,
    batch_size: int,
    num_workers: int,
    image_size: int,
    val_split: float,
    max_train: int,
    max_val: int,
    probe_timeout_sec: float,
    progress_every: int,
    max_seconds_per_model: int,
    freeze_backbone: bool,
    pretrained: bool,
) -> float | None:
    _print_header("🖼️ REAL/FAKE CLASSIFIER - FULL RAW VISION DATASET")

    real_dir = raw_vision_root / "train_real"
    fake_dir = raw_vision_root / "train_fake"

    real_images = _collect_images_recursive(real_dir)
    fake_images = _collect_images_recursive(fake_dir)

    all_images = real_images + fake_images
    all_labels = [0] * len(real_images) + [1] * len(fake_images)

    _log(f"📊 Total samples: {len(all_images):,}")
    _log(f"📊 Class distribution: {Counter(all_labels)}")

    if not all_images:
        _log("❌ No raw vision data found.")
        _log(f"   Expected: {raw_vision_root}/train_real/**/*.(jpg|png)")
        _log(f"   Expected: {raw_vision_root}/train_fake/**/*.(jpg|png)")
        return None

    from sklearn.model_selection import train_test_split

    train_imgs, val_imgs, train_lbls, val_lbls = train_test_split(
        all_images, all_labels, test_size=val_split, random_state=int(seed), stratify=all_labels
    )

    train_imgs, train_lbls = _cap_pairs(train_imgs, train_lbls, limit=int(max_train), seed=int(seed))
    val_imgs, val_lbls = _cap_pairs(val_imgs, val_lbls, limit=int(max_val), seed=int(seed) + 1)
    train_imgs, train_lbls = _filter_readable_pairs(
        train_imgs,
        train_lbls,
        timeout_sec=float(probe_timeout_sec),
        stage="realfake-train",
    )
    val_imgs, val_lbls = _filter_readable_pairs(
        val_imgs,
        val_lbls,
        timeout_sec=float(probe_timeout_sec),
        stage="realfake-val",
    )

    _log(f"📊 Training: {len(train_imgs):,} | Validation: {len(val_imgs):,}")
    if not train_imgs:
        _log("❌ No readable train images remained after probing.")
        return None
    if not val_imgs:
        _log("❌ No readable validation images remained after probing.")
        return None

    train_transform = transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.RandomHorizontalFlip(0.5),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )
    val_transform = transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )

    train_dataset = ImageDataset(train_imgs, train_lbls, train_transform, image_size)
    val_dataset = ImageDataset(val_imgs, val_lbls, val_transform, image_size)

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=False,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=False,
    )

    weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1 if pretrained else None
    try:
        model = models.efficientnet_b0(weights=weights)
    except Exception as exc:
        if not pretrained:
            raise
        _log(
            "⚠️  Could not load pretrained EfficientNet-B0 weights; "
            f"falling back to random init. ({exc})"
        )
        model = models.efficientnet_b0(weights=None)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, 2)
    if freeze_backbone:
        for p in model.features.parameters():
            p.requires_grad = False
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    trainable = [p for p in model.parameters() if p.requires_grad]
    optimizer = optim.AdamW(trainable, lr=0.001, weight_decay=0.01)
    scheduler = optim.lr_scheduler.OneCycleLR(
        optimizer, max_lr=0.003, steps_per_epoch=len(train_loader), epochs=epochs
    )

    best_acc = -1.0
    best_path = out_dir / "realfake_full.pt"
    run_start = time.monotonic()

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

            if batch_idx % max(1, int(progress_every)) == 0 or batch_idx + 1 == len(train_loader):
                acc = 100.0 * correct / max(1, total)
                _log(
                    f"  Epoch {epoch+1}/{epochs} | Batch {batch_idx}/{len(train_loader)} | "
                    f"Loss: {loss.item():.4f} | Acc: {acc:.2f}%"
                )
            if int(max_seconds_per_model) > 0 and (time.monotonic() - run_start) > int(
                max_seconds_per_model
            ):
                _log(
                    f"⏱️  Reached --max-seconds-per-model={max_seconds_per_model}; "
                    "stopping real/fake training early."
                )
                break

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
        _log(f"📈 Epoch {epoch+1} - Train Acc: {train_acc:.2f}% | Val Acc: {val_acc:.2f}%")

        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), best_path)
        if int(max_seconds_per_model) > 0 and (time.monotonic() - run_start) > int(
            max_seconds_per_model
        ):
            break

    _log(f"\n✅ REAL/FAKE BEST ACCURACY: {best_acc:.2f}%")
    _log(f"📁 Saved: {best_path}")
    return best_acc


def main() -> int:
    parser = argparse.ArgumentParser(description="Train full vision models (deepfake + real/fake).")
    parser.add_argument("--device", default="auto", help="auto|cpu|cuda|mps")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--epochs", type=int, default=3, help="Epochs per model.")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size.")
    parser.add_argument("--num-workers", type=int, default=0, help="DataLoader workers.")
    parser.add_argument(
        "--val-split", type=float, default=0.15, help="Validation split for real/fake dataset."
    )
    parser.add_argument(
        "--max-train", type=int, default=0, help="Cap training samples (0 = no cap)."
    )
    parser.add_argument(
        "--max-val", type=int, default=0, help="Cap validation samples (0 = no cap)."
    )
    parser.add_argument("--image-size", type=int, default=160, help="Resize images to NxN.")
    parser.add_argument(
        "--progress-every",
        type=int,
        default=10,
        help="Log every N training batches.",
    )
    parser.add_argument(
        "--probe-timeout-sec",
        type=float,
        default=1.0,
        help="Per-file readability probe timeout in seconds before training.",
    )
    parser.add_argument(
        "--max-seconds-per-model",
        type=int,
        default=0,
        help="Optional wall-clock cap per model (0 disables).",
    )
    parser.add_argument(
        "--freeze-backbone",
        action="store_true",
        help="Freeze backbone and train classifier head only (faster on CPU).",
    )
    parser.add_argument(
        "--no-pretrained", action="store_true", help="Disable ImageNet pretrained weights."
    )

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
    parser.add_argument(
        "--realfake", action="store_true", help="Train real/fake model (raw vision)."
    )
    args = parser.parse_args()

    if args.epochs <= 0:
        raise SystemExit("--epochs must be >= 1")
    if args.batch_size <= 0:
        raise SystemExit("--batch-size must be >= 1")
    if args.image_size < 64:
        raise SystemExit("--image-size must be >= 64")
    if args.num_workers < 0:
        raise SystemExit("--num-workers must be >= 0")
    if not (0.0 < float(args.val_split) < 1.0):
        raise SystemExit("--val-split must be between 0 and 1")

    device = _resolve_device(args.device)
    _set_seed(int(args.seed))
    # Keep CPU runs predictable in constrained environments.
    torch.set_num_threads(max(1, int(torch.get_num_threads())))

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    celeb_root = Path(args.celeb_root).expanduser().resolve()
    raw_vision_root = Path(args.raw_vision_root).expanduser().resolve()
    pretrained = not bool(args.no_pretrained)

    selected = {k for k, v in {"deepfake": args.deepfake, "realfake": args.realfake}.items() if v}
    if not selected:
        selected = {"deepfake", "realfake"}

    _log(f"🚀 FULL VISION TRAINING - Device: {device}")
    _log(f"📁 Output dir: {out_dir}")
    _log(
        f"🔁 Epochs: {args.epochs} | Batch size: {args.batch_size} | "
        f"Workers: {args.num_workers} | Image size: {args.image_size}"
    )
    _log(
        f"🧪 Probe timeout: {args.probe_timeout_sec}s | Progress every: {args.progress_every} batches | "
        f"Freeze backbone: {bool(args.freeze_backbone)}"
    )
    _log("=" * 60)

    results: dict[str, float] = {}

    if "deepfake" in selected:
        acc = train_deepfake_full(
            device=device,
            out_dir=out_dir,
            celeb_root=celeb_root,
            seed=int(args.seed),
            epochs=int(args.epochs),
            batch_size=int(args.batch_size),
            num_workers=int(args.num_workers),
            image_size=int(args.image_size),
            max_train=int(args.max_train),
            max_val=int(args.max_val),
            probe_timeout_sec=float(args.probe_timeout_sec),
            progress_every=int(args.progress_every),
            max_seconds_per_model=int(args.max_seconds_per_model),
            freeze_backbone=bool(args.freeze_backbone),
            pretrained=pretrained,
        )
        if acc is not None:
            results["deepfake"] = float(acc)

    if "realfake" in selected:
        acc = train_realfake_full(
            device=device,
            out_dir=out_dir,
            raw_vision_root=raw_vision_root,
            seed=int(args.seed),
            epochs=int(args.epochs),
            batch_size=int(args.batch_size),
            num_workers=int(args.num_workers),
            image_size=int(args.image_size),
            val_split=float(args.val_split),
            max_train=int(args.max_train),
            max_val=int(args.max_val),
            probe_timeout_sec=float(args.probe_timeout_sec),
            progress_every=int(args.progress_every),
            max_seconds_per_model=int(args.max_seconds_per_model),
            freeze_backbone=bool(args.freeze_backbone),
            pretrained=pretrained,
        )
        if acc is not None:
            results["realfake"] = float(acc)

    _print_header("🎯 FULL VISION TRAINING COMPLETE")
    if not results:
        return 1
    for name, acc in results.items():
        status = "✅" if acc >= 95 else "⚠️"
        _log(f"{status} {name}: {acc:.2f}%")
    avg = sum(results.values()) / len(results)
    _log(f"\n📊 AVERAGE VISION ACCURACY: {avg:.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
