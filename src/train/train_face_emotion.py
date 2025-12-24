"""Train a 7-class face emotion classifier (image) for offline inference.

Expected dataset layout (recommended):
  data/raw/vision/face_emotion/
    train/
      angry/ ...images...
      disgust/ ...
      fear/ ...
      happy/ ...
      sad/ ...
      surprise/ ...
      neutral/ ...
    val/
      angry/ ...
      ...

If `train/` and `val/` are not present, the script treats `--data-dir` as an
ImageFolder root (class subfolders) and splits train/val automatically.

Output artifacts:
  models/vision/face_emotion/model.pt
  models/vision/face_emotion/classes.txt
"""

from __future__ import annotations

import argparse
import json
import os
import random
from dataclasses import dataclass
from pathlib import Path


_DEFAULT_OUT_DIR = Path("models/vision/face_emotion")
_EXPECTED_EMOTIONS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]
_DEFAULT_NUMERIC_LABEL_MAP_1_TO_7 = {
    # Common FER-style mapping with labels starting at 1.
    "1": "angry",
    "2": "disgust",
    "3": "fear",
    "4": "happy",
    "5": "sad",
    "6": "surprise",
    "7": "neutral",
}
_DEFAULT_NUMERIC_LABEL_MAP_0_TO_6 = {
    # Same mapping but 0-indexed.
    "0": "angry",
    "1": "disgust",
    "2": "fear",
    "3": "happy",
    "4": "sad",
    "5": "surprise",
    "6": "neutral",
}


def _resolve_device(requested: str | None) -> str:
    req = (requested or "").strip()
    if not req or req.lower() == "auto":
        try:  # pragma: no cover - depends on local hardware
            import torch

            if torch.backends.mps.is_available():
                return "mps"
            if torch.cuda.is_available():
                return "cuda"
        except Exception:
            pass
        return "cpu"
    return req


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except Exception:
        pass
    try:
        import torch

        torch.manual_seed(seed)
    except Exception:
        pass


@dataclass(frozen=True)
class SplitRoots:
    train_root: Path
    val_root: Path | None


def _normalize_data_dir(data_dir: Path) -> Path:
    """Handle common archive layouts (e.g., DATASET/train + DATASET/test)."""
    if (data_dir / "train").exists():
        return data_dir
    if (data_dir / "DATASET" / "train").exists():
        return data_dir / "DATASET"
    children = [p for p in data_dir.iterdir() if p.is_dir()]
    if len(children) == 1 and (children[0] / "train").exists():
        return children[0]
    return data_dir


def _detect_split_roots(data_dir: Path) -> SplitRoots:
    data_dir = _normalize_data_dir(data_dir)
    train_root = data_dir / "train"
    val_root = data_dir / "val"
    test_root = data_dir / "test"
    if train_root.exists() and train_root.is_dir():
        if val_root.exists() and val_root.is_dir():
            return SplitRoots(train_root=train_root, val_root=val_root)
        if test_root.exists() and test_root.is_dir():
            return SplitRoots(train_root=train_root, val_root=test_root)
        return SplitRoots(train_root=train_root, val_root=None)
    return SplitRoots(train_root=data_dir, val_root=None)


def _parse_label_map(raw: str | None) -> dict[str, str] | None:
    if not raw or not raw.strip():
        return None
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("--label-map must be valid JSON (a dict of {\"source\": \"label\"}).") from exc
    if not isinstance(obj, dict) or not obj:
        raise ValueError("--label-map must be a non-empty JSON object.")
    out: dict[str, str] = {}
    for k, v in obj.items():
        if k is None or v is None:
            continue
        out[str(k)] = str(v)
    return out or None


def _auto_map_numeric_classes(raw_classes: list[str]) -> list[str]:
    # Keep stable mapping order (ImageFolder sorts by folder name, so 0..6 or 1..7 is stable).
    if set(raw_classes) == set(_DEFAULT_NUMERIC_LABEL_MAP_1_TO_7.keys()):
        return [_DEFAULT_NUMERIC_LABEL_MAP_1_TO_7[c] for c in raw_classes]
    if set(raw_classes) == set(_DEFAULT_NUMERIC_LABEL_MAP_0_TO_6.keys()):
        return [_DEFAULT_NUMERIC_LABEL_MAP_0_TO_6[c] for c in raw_classes]
    return raw_classes


def _maybe_limit_indices(indices: list[int], *, max_items: int, seed: int) -> list[int]:
    if max_items <= 0 or max_items >= len(indices):
        return indices
    rng = random.Random(seed)
    out = list(indices)
    rng.shuffle(out)
    return out[:max_items]


def _build_model(arch: str, *, num_classes: int, pretrained: bool) -> "object":
    import torch
    from torch import nn
    from torchvision import models

    arch = (arch or "small_cnn").strip().lower()
    if arch == "resnet18":
        weights = models.ResNet18_Weights.DEFAULT if pretrained else None
        model = models.resnet18(weights=weights)
        in_feat = int(model.fc.in_features)
        model.fc = nn.Linear(in_feat, num_classes)
        return model
    if arch != "small_cnn":
        raise ValueError("arch must be one of: small_cnn, resnet18")

    class SmallCNN(nn.Module):
        def __init__(self, classes: int):
            super().__init__()
            self.features = nn.Sequential(
                nn.Conv2d(3, 32, 3, padding=1),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(2),
                nn.Conv2d(32, 64, 3, padding=1),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(2),
                nn.Conv2d(64, 128, 3, padding=1),
                nn.ReLU(inplace=True),
                nn.AdaptiveAvgPool2d((1, 1)),
            )
            self.classifier = nn.Linear(128, classes)

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            x = self.features(x)
            x = x.flatten(1)
            return self.classifier(x)

    return SmallCNN(num_classes)


def _train_one_epoch(*, model, loader, device, optimizer, loss_fn) -> tuple[float, float]:
    import torch

    model.train()
    total_loss = 0.0
    correct = 0
    total = 0
    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)
        optimizer.zero_grad(set_to_none=True)
        logits = model(images)
        loss = loss_fn(logits, labels)
        loss.backward()
        optimizer.step()
        total_loss += float(loss.item()) * int(labels.size(0))
        preds = torch.argmax(logits, dim=1)
        correct += int((preds == labels).sum().item())
        total += int(labels.size(0))
    avg_loss = total_loss / max(1, total)
    acc = correct / max(1, total)
    return avg_loss, acc


def _evaluate(*, model, loader, device, loss_fn) -> tuple[float, float]:  # pragma: no cover - exercised via training
    import torch

    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)
            logits = model(images)
            loss = loss_fn(logits, labels)
            total_loss += float(loss.item()) * int(labels.size(0))
            preds = torch.argmax(logits, dim=1)
            correct += int((preds == labels).sum().item())
            total += int(labels.size(0))
    avg_loss = total_loss / max(1, total)
    acc = correct / max(1, total)
    return avg_loss, acc


def main() -> int:
    ap = argparse.ArgumentParser(description="Train a face emotion classifier (7 classes).")
    ap.add_argument("--data-dir", type=Path, default=Path("data/raw/vision/face_emotion"))
    ap.add_argument("--out-dir", type=Path, default=_DEFAULT_OUT_DIR)
    ap.add_argument("--arch", choices=["small_cnn", "resnet18"], default="small_cnn")
    ap.add_argument("--pretrained", action="store_true", help="Use pretrained ImageNet weights (resnet18 only).")
    ap.add_argument("--image-size", type=int, default=96, help="Resize images to NxN.")
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--num-workers", type=int, default=0)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--weight-decay", type=float, default=1e-4)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--device", type=str, default=os.getenv("UAIS_FACE_EMOTION_DEVICE", "auto"))
    ap.add_argument("--val-split", type=float, default=0.15, help="Used only when val/ is not present.")
    ap.add_argument(
        "--label-map",
        type=str,
        default=os.getenv("UAIS_FACE_EMOTION_LABEL_MAP", ""),
        help="Optional JSON mapping from dataset folder names to emotion labels.",
    )
    ap.add_argument("--max-train", type=int, default=0, help="Cap training samples (0 = no cap).")
    ap.add_argument("--max-val", type=int, default=0, help="Cap validation samples (0 = no cap).")
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"[face-emotion] Missing dataset dir: {data_dir}")
        print("Expected an ImageFolder layout (class subfolders) or train/val split.")
        return 2

    _seed_everything(int(args.seed))

    try:
        import torch
        from torch import nn
        from torch.utils.data import DataLoader, Subset
        from torchvision import datasets, transforms
    except Exception as exc:
        raise RuntimeError(f"Missing torch/torchvision deps: {exc}") from exc

    split = _detect_split_roots(data_dir)
    img_size = int(args.image_size)
    if args.arch == "resnet18" and img_size < 128:
        print("[face-emotion] Note: resnet18 typically performs better with image-size >= 160.")

    def _to_rgb(im):
        return im.convert("RGB")

    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]
    train_tfms = transforms.Compose(
        [
            transforms.Resize((img_size, img_size)),
            transforms.Lambda(_to_rgb),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=10),
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std),
        ]
    )
    val_tfms = transforms.Compose(
        [
            transforms.Resize((img_size, img_size)),
            transforms.Lambda(_to_rgb),
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std),
        ]
    )

    raw_classes: list[str]
    if split.val_root is not None:
        train_ds = datasets.ImageFolder(split.train_root, transform=train_tfms)
        val_ds = datasets.ImageFolder(split.val_root, transform=val_tfms)
        if train_ds.classes != val_ds.classes:
            raise RuntimeError(
                f"Train/val class mismatch. train={train_ds.classes} val={val_ds.classes}. "
                "Ensure both splits contain the same folders."
            )
        raw_classes = list(train_ds.classes)
    else:
        root_train = datasets.ImageFolder(split.train_root, transform=train_tfms)
        root_val = datasets.ImageFolder(split.train_root, transform=val_tfms)
        raw_classes = list(root_train.classes)

        if not (0.0 < float(args.val_split) < 1.0):
            raise ValueError("--val-split must be in (0, 1) when val/ is not present.")
        n = len(root_train)
        if n < 10:
            raise RuntimeError("Not enough images to split train/val (need at least 10).")
        val_n = max(1, int(round(n * float(args.val_split))))
        train_n = max(1, n - val_n)
        gen = torch.Generator().manual_seed(int(args.seed))
        perm = torch.randperm(n, generator=gen).tolist()
        val_indices = perm[:val_n]
        train_indices = perm[val_n : val_n + train_n]
        train_ds = Subset(root_train, train_indices)
        val_ds = Subset(root_val, val_indices)

    label_map = _parse_label_map(str(args.label_map) if args.label_map else None)
    if label_map is not None:
        classes = [label_map.get(c, c) for c in raw_classes]
    else:
        classes = _auto_map_numeric_classes(raw_classes)

    expected = {e.lower() for e in _EXPECTED_EMOTIONS}
    found = {c.lower() for c in classes}
    if found != expected:
        missing = sorted(expected.difference(found))
        extra = sorted(found.difference(expected))
        print("[face-emotion] Warning: dataset classes do not match the canonical 7 emotions.")
        print(f"  expected: {sorted(expected)}")
        print(f"  found:    {sorted(found)}")
        if missing:
            print(f"  missing:  {missing}")
        if extra:
            print(f"  extra:    {extra}")

    # Apply optional caps.
    if int(args.max_train) > 0:
        idxs = list(range(len(train_ds)))
        keep = _maybe_limit_indices(idxs, max_items=int(args.max_train), seed=int(args.seed))
        train_ds = Subset(train_ds, keep)
    if int(args.max_val) > 0:
        idxs = list(range(len(val_ds)))
        keep = _maybe_limit_indices(idxs, max_items=int(args.max_val), seed=int(args.seed) + 1)
        val_ds = Subset(val_ds, keep)

    train_loader = DataLoader(
        train_ds,
        batch_size=int(args.batch_size),
        shuffle=True,
        num_workers=int(args.num_workers),
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=int(args.batch_size),
        shuffle=False,
        num_workers=int(args.num_workers),
    )

    device = torch.device(_resolve_device(str(args.device)))
    model = _build_model(str(args.arch), num_classes=len(classes), pretrained=bool(args.pretrained)).to(device)

    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(args.lr),
        weight_decay=float(args.weight_decay),
    )

    print(
        "[face-emotion] config:",
        {
            "data_dir": str(data_dir),
            "train_root": str(split.train_root),
            "val_root": str(split.val_root) if split.val_root is not None else None,
            "raw_classes": raw_classes,
            "classes": classes,
            "arch": args.arch,
            "pretrained": bool(args.pretrained),
            "image_size": img_size,
            "epochs": int(args.epochs),
            "batch_size": int(args.batch_size),
            "device": str(device),
            "train_samples": len(train_ds),
            "val_samples": len(val_ds),
        },
    )

    best_val_acc = -1.0
    best_state = None
    history: list[dict[str, float]] = []

    for epoch in range(1, int(args.epochs) + 1):
        tr_loss, tr_acc = _train_one_epoch(
            model=model,
            loader=train_loader,
            device=device,
            optimizer=optimizer,
            loss_fn=loss_fn,
        )
        va_loss, va_acc = _evaluate(model=model, loader=val_loader, device=device, loss_fn=loss_fn)
        history.append(
            {
                "epoch": float(epoch),
                "train_loss": float(tr_loss),
                "train_acc": float(tr_acc),
                "val_loss": float(va_loss),
                "val_acc": float(va_acc),
            }
        )
        print(
            f"[face-emotion] epoch {epoch}/{int(args.epochs)} "
            f"train_loss={tr_loss:.4f} train_acc={tr_acc:.3f} val_loss={va_loss:.4f} val_acc={va_acc:.3f}"
        )
        if va_acc >= best_val_acc:
            best_val_acc = float(va_acc)
            best_state = {k: v.detach().cpu() for k, v in model.state_dict().items()}

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / "model.pt"
    classes_path = out_dir / "classes.txt"
    metrics_path = out_dir / "metrics.json"

    if best_state is None:
        best_state = {k: v.detach().cpu() for k, v in model.state_dict().items()}

    torch.save(
        {
            "arch": str(args.arch),
            "pretrained": bool(args.pretrained),
            "image_size": int(img_size),
            "classes": classes,
            "raw_classes": raw_classes,
            "mean": mean,
            "std": std,
            "state_dict": best_state,
        },
        model_path,
    )
    classes_path.write_text("\n".join(classes) + "\n", encoding="utf-8")
    metrics_path.write_text(
        json.dumps(
            {
                "best_val_acc": best_val_acc,
                "history": history,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"[face-emotion] Saved: {model_path}")
    print(f"[face-emotion] Saved: {classes_path}")
    print(f"[face-emotion] Saved: {metrics_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
