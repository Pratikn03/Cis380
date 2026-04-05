"""Prepare vision training folders from whatever is under `data/raw/vision/datasets`.

Why this exists
--------------
Some training code expects a binary real-vs-fake folder layout:

- data/raw/vision/train_real/
- data/raw/vision/train_fake/

But the repo may contain a different vision dataset under:

- data/raw/vision/datasets/

This script:
- Recursively scans `data/raw/vision/datasets` for images
- Copies images into train_real/train_fake based on path keyword routing
- Reports counts and an "unclassified" bucket
- Heuristically warns if the dataset looks like Intel Image Classification (scene classes)

Notes
-----
- Files are COPIED (not moved) to preserve the original dataset.
- Name collisions are handled by de-duping with a short hash suffix.

Usage
-----
python scripts/prepare_vision_data.py
python scripts/prepare_vision_data.py --src data/raw/vision/datasets --limit 5000
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

REAL_KEYS = [
    "real",
    "auth",
    "authentic",
    "pristine",
    "original",
    "bonafide",
    "bona_fide",
    "genuine",
]

FAKE_KEYS = [
    "fake",
    "forg",
    "forged",
    "manip",
    "tamper",
    "synth",
    "generated",
    "deepfake",
    "spoof",
]

# Intel Image Classification dataset often has these folder names
INTEL_SCENE_HINTS = {"buildings", "forest", "glacier", "mountain", "sea", "street"}


def _deduped_dest(out_dir: Path, src_path: Path) -> Path:
    """Return a destination path that won't overwrite existing by adding a hash if needed."""
    candidate = out_dir / src_path.name
    if not candidate.exists():
        return candidate

    h = hashlib.sha1(str(src_path).encode("utf-8")).hexdigest()[:8]
    return out_dir / f"{src_path.stem}_{h}{src_path.suffix}"


def _looks_like_intel_scene_dataset(src_root: Path) -> bool:
    # Look at the first couple levels of directory names.
    dirs = {p.name.lower() for p in src_root.rglob("*") if p.is_dir()}
    hits = len(INTEL_SCENE_HINTS.intersection(dirs))
    return hits >= 3


def prepare(
    *,
    src: Path,
    out_root: Path,
    copy: bool = True,
    limit: int | None = None,
) -> dict:
    train_real = out_root / "train_real"
    train_fake = out_root / "train_fake"
    train_real.mkdir(parents=True, exist_ok=True)
    train_fake.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        raise FileNotFoundError(f"Source vision datasets folder not found: {src}")

    # Safety: avoid scanning the output root (or train_real/train_fake) because it will
    # re-copy into itself and create duplicates via the de-dupe logic.
    src_resolved = src.resolve()
    out_resolved = out_root.resolve()
    bad_roots = {
        out_resolved,
        (out_resolved / "train_real").resolve(),
        (out_resolved / "train_fake").resolve(),
    }
    if src_resolved in bad_roots:
        raise ValueError(
            f"Refusing to use src={src} because it is the output directory. "
            "Pass a dataset folder (e.g. data/raw/vision/datasets/<name>) instead."
        )

    images = [p for p in src.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
    if limit is not None:
        images = images[:limit]

    real_ct = fake_ct = unk_ct = 0
    collisions = 0

    for p in images:
        rel = str(p).lower()
        is_real = any(k in rel for k in REAL_KEYS)
        is_fake = any(k in rel for k in FAKE_KEYS)

        if is_real and not is_fake:
            dest_dir = train_real
            real_ct += 1
        elif is_fake and not is_real:
            dest_dir = train_fake
            fake_ct += 1
        else:
            unk_ct += 1
            continue

        dest = _deduped_dest(dest_dir, p)
        if dest.name != p.name:
            collisions += 1

        if copy:
            shutil.copy2(p, dest)
        else:
            shutil.move(p, dest)

    looks_like_intel = _looks_like_intel_scene_dataset(src)

    return {
        "src": str(src),
        "total_images_found": len(images),
        "copied_train_real": real_ct,
        "copied_train_fake": fake_ct,
        "unclassified": unk_ct,
        "name_collisions_deduped": collisions,
        "looks_like_intel_scene_dataset": looks_like_intel,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare vision train_real/train_fake folders")
    parser.add_argument("--src", type=Path, default=Path("data/raw/vision/datasets"))
    parser.add_argument("--out-root", type=Path, default=Path("data/raw/vision"))
    parser.add_argument("--limit", type=int, default=None, help="Optional limit for quick tests")
    args = parser.parse_args()

    stats = prepare(src=args.src, out_root=args.out_root, limit=args.limit)

    print("VISION PREP SUMMARY")
    print("-------------------")
    for k, v in stats.items():
        print(f"{k}: {v}")

    if stats["looks_like_intel_scene_dataset"]:
        print(
            "\nNOTE: The dataset structure looks like Intel Image Classification (scene categories).\n"
            "If you don't have explicit real/fake labels, consider training in multi-class scene mode\n"
            "on the original folder structure instead of using train_real/train_fake.\n"
            "(This script still helps if your dataset paths contain real/fake keywords, but\n"
            "unclassified may be high for scene datasets.)"
        )


if __name__ == "__main__":
    main()
