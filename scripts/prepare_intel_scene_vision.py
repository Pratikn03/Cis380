"""Prepare Intel Scene Image Classification dataset for UAIS-V PyTorch trainer.

Your repo contains the Kaggle-style Intel Image Classification dataset under:

  data/raw/vision/datasets/puneet6060/intel-image-classification/versions/2/

This dataset uses these folders:
  seg_train/seg_train/<class>/*.jpg
  seg_test/seg_test/<class>/*.jpg
  seg_pred/seg_pred/*.jpg (unlabeled)

But `uais_v.training.train_vision` expects an ImageFolder layout:
  <data_dir>/train/<class>/*.jpg
  <data_dir>/val/<class>/*.jpg

This script copies (not moves) Intel images into:
  data/raw/vision/intel_scene/train/
  data/raw/vision/intel_scene/val/

It de-dupes filename collisions by adding a short hash suffix.

Usage:
  python scripts/prepare_intel_scene_vision.py
  python scripts/prepare_intel_scene_vision.py --src data/raw/vision/datasets/.../versions/2
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path


IMAGE_EXTS = {".jpg", ".jpeg", ".png"}


def _deduped_dest(out_dir: Path, src: Path) -> Path:
    candidate = out_dir / src.name
    if not candidate.exists():
        return candidate
    h = hashlib.sha1(str(src).encode("utf-8")).hexdigest()[:8]
    return out_dir / f"{src.stem}_{h}{src.suffix}"


def _copy_tree(src_root: Path, dst_root: Path) -> int:
    count = 0
    for p in src_root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in IMAGE_EXTS:
            continue
        # class is parent folder name (e.g., forest)
        cls = p.parent.name
        out_dir = dst_root / cls
        out_dir.mkdir(parents=True, exist_ok=True)
        dest = _deduped_dest(out_dir, p)
        shutil.copy2(p, dest)
        count += 1
    return count


def prepare(*, src_version_dir: Path, out_dir: Path) -> dict:
    # Intel dataset nests images under seg_train/seg_train and seg_test/seg_test
    train_src = src_version_dir / "seg_train" / "seg_train"
    val_src = src_version_dir / "seg_test" / "seg_test"

    if not train_src.exists():
        raise FileNotFoundError(f"Expected Intel train folder not found: {train_src}")
    if not val_src.exists():
        raise FileNotFoundError(f"Expected Intel test folder not found: {val_src}")

    train_out = out_dir / "train"
    val_out = out_dir / "val"
    train_out.mkdir(parents=True, exist_ok=True)
    val_out.mkdir(parents=True, exist_ok=True)

    train_ct = _copy_tree(train_src, train_out)
    val_ct = _copy_tree(val_src, val_out)

    classes = sorted({p.name for p in train_out.iterdir() if p.is_dir()})

    return {
        "src_version_dir": str(src_version_dir),
        "out_dir": str(out_dir),
        "train_images_copied": train_ct,
        "val_images_copied": val_ct,
        "num_classes": len(classes),
        "classes": classes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare Intel scene dataset into train/val ImageFolder layout"
    )
    parser.add_argument(
        "--src",
        type=Path,
        default=Path("data/raw/vision/datasets/puneet6060/intel-image-classification/versions/2"),
    )
    parser.add_argument("--out", type=Path, default=Path("data/raw/vision/intel_scene"))
    args = parser.parse_args()

    stats = prepare(src_version_dir=args.src, out_dir=args.out)

    print("INTEL SCENE PREP SUMMARY")
    print("------------------------")
    for k, v in stats.items():
        if k == "classes":
            continue
        print(f"{k}: {v}")
    print("classes:", ", ".join(stats["classes"]))


if __name__ == "__main__":
    main()
