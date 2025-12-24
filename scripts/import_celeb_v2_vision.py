"""Import Celeb-DF/Celeb_V2 extracted frames into OmniChatX vision folders.

This keeps your original dataset intact and *copies or hardlinks* images into:

- data/raw/vision/train_real/
- data/raw/vision/train_fake/

and prepares a train/val ImageFolder layout for the PyTorch trainer:

- data/processed/vision/train/{real,fake}
- data/processed/vision/val/{real,fake}

Expected source layout (common in extracted frame exports):

data/Celeb_V2/
  Train/{real,fake}/*.jpg
  Val/{real,fake}/*.jpg
  Test/{real,fake}/*.jpg  (optional)

Usage:
  python scripts/import_celeb_v2_vision.py
  python scripts/import_celeb_v2_vision.py --src data/Celeb_V2 --mode link
  python scripts/import_celeb_v2_vision.py --include-test
  python scripts/import_celeb_v2_vision.py --cap 20000
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
from dataclasses import dataclass
from pathlib import Path


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


@dataclass
class ImportStats:
    scanned: int = 0
    linked: int = 0
    copied: int = 0
    skipped_existing: int = 0
    collisions_deduped: int = 0


def _deduped_dest(out_dir: Path, src_path: Path) -> Path:
    candidate = out_dir / src_path.name
    if not candidate.exists():
        return candidate
    h = hashlib.sha1(str(src_path).encode("utf-8")).hexdigest()[:8]
    return out_dir / f"{src_path.stem}_{h}{src_path.suffix}"


def _link_or_copy(src: Path, dst: Path, *, mode: str) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return "skipped"

    if mode == "copy":
        shutil.copy2(src, dst)
        return "copied"

    # mode == "link" (default): try hardlink for zero extra disk; fallback to copy.
    try:
        os.link(src, dst)
        return "linked"
    except OSError:
        shutil.copy2(src, dst)
        return "copied"


def _iter_images(root: Path):
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            yield p


def _import_split(
    *,
    src_dir: Path,
    dst_dir: Path,
    mode: str,
    cap: int | None,
    stats: ImportStats,
) -> None:
    count = 0
    for src in _iter_images(src_dir):
        stats.scanned += 1
        if cap is not None and count >= cap:
            break
        dst = _deduped_dest(dst_dir, src)
        if dst.name != src.name:
            stats.collisions_deduped += 1
        action = _link_or_copy(src, dst, mode=mode)
        if action == "skipped":
            stats.skipped_existing += 1
        elif action == "linked":
            stats.linked += 1
        else:
            stats.copied += 1
        count += 1


def _resolve_source_layout(src: Path) -> dict[str, Path]:
    """Return split/class directories when the expected layout exists."""
    expected = {}
    for split in ("Train", "Val", "Test"):
        for cls in ("real", "fake"):
            p = src / split / cls
            if p.exists():
                expected[f"{split.lower()}_{cls}"] = p
    if (
        expected.get("train_real")
        and expected.get("train_fake")
        and expected.get("val_real")
        and expected.get("val_fake")
    ):
        return expected
    raise FileNotFoundError(
        "Could not find expected Celeb_V2 layout under "
        f"{src}. Expected at least Train/real, Train/fake, Val/real, Val/fake."
    )


def run(*, src: Path, mode: str, cap: int | None, include_test: bool) -> dict[str, object]:
    layout = _resolve_source_layout(src)

    raw_root = Path("data/raw/vision")
    processed_root = Path("data/processed/vision")

    # Raw (binary) expected folders: keep split subfolders to avoid collisions.
    raw_real_train = raw_root / "train_real" / "train"
    raw_fake_train = raw_root / "train_fake" / "train"
    raw_real_val = raw_root / "train_real" / "val"
    raw_fake_val = raw_root / "train_fake" / "val"
    raw_real_test = raw_root / "train_real" / "test"
    raw_fake_test = raw_root / "train_fake" / "test"

    # Processed ImageFolder layout for trainer.
    proc_train_real = processed_root / "train" / "real"
    proc_train_fake = processed_root / "train" / "fake"
    proc_val_real = processed_root / "val" / "real"
    proc_val_fake = processed_root / "val" / "fake"
    proc_test_real = processed_root / "test" / "real"
    proc_test_fake = processed_root / "test" / "fake"

    stats = ImportStats()

    # Train split
    _import_split(
        src_dir=layout["train_real"], dst_dir=raw_real_train, mode=mode, cap=cap, stats=stats
    )
    _import_split(
        src_dir=layout["train_fake"], dst_dir=raw_fake_train, mode=mode, cap=cap, stats=stats
    )
    _import_split(
        src_dir=layout["train_real"], dst_dir=proc_train_real, mode=mode, cap=cap, stats=stats
    )
    _import_split(
        src_dir=layout["train_fake"], dst_dir=proc_train_fake, mode=mode, cap=cap, stats=stats
    )

    # Val split
    _import_split(src_dir=layout["val_real"], dst_dir=raw_real_val, mode=mode, cap=cap, stats=stats)
    _import_split(src_dir=layout["val_fake"], dst_dir=raw_fake_val, mode=mode, cap=cap, stats=stats)
    _import_split(
        src_dir=layout["val_real"], dst_dir=proc_val_real, mode=mode, cap=cap, stats=stats
    )
    _import_split(
        src_dir=layout["val_fake"], dst_dir=proc_val_fake, mode=mode, cap=cap, stats=stats
    )

    # Optional test split
    if include_test and layout.get("test_real") and layout.get("test_fake"):
        _import_split(
            src_dir=layout["test_real"], dst_dir=raw_real_test, mode=mode, cap=cap, stats=stats
        )
        _import_split(
            src_dir=layout["test_fake"], dst_dir=raw_fake_test, mode=mode, cap=cap, stats=stats
        )
        _import_split(
            src_dir=layout["test_real"], dst_dir=proc_test_real, mode=mode, cap=cap, stats=stats
        )
        _import_split(
            src_dir=layout["test_fake"], dst_dir=proc_test_fake, mode=mode, cap=cap, stats=stats
        )

    # Counts (recursive)
    def count_imgs(p: Path) -> int:
        return sum(1 for _ in _iter_images(p)) if p.exists() else 0

    out = {
        "src": str(src),
        "mode": mode,
        "cap": cap,
        "include_test": include_test,
        "stats": stats.__dict__,
        "raw_train_real_images": count_imgs(raw_root / "train_real"),
        "raw_train_fake_images": count_imgs(raw_root / "train_fake"),
        "processed_train_images": count_imgs(processed_root / "train"),
        "processed_val_images": count_imgs(processed_root / "val"),
        "processed_test_images": count_imgs(processed_root / "test") if include_test else 0,
    }
    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import Celeb_V2 frames into OmniChatX vision folders."
    )
    parser.add_argument("--src", type=Path, default=Path("data/Celeb_V2"))
    parser.add_argument(
        "--mode",
        choices=["link", "copy"],
        default="link",
        help="Use hardlinks (default, saves disk) or copy files.",
    )
    parser.add_argument(
        "--cap",
        type=int,
        default=None,
        help="Optional cap per split/class (e.g. 20000). Applies independently to each split/class.",
    )
    parser.add_argument(
        "--include-test", action="store_true", help="Also import Test split into raw+processed."
    )
    args = parser.parse_args()

    out = run(src=args.src, mode=args.mode, cap=args.cap, include_test=args.include_test)

    print("CELEB_V2 IMPORT SUMMARY")
    print("-----------------------")
    for k, v in out.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
