from __future__ import annotations

import argparse
from collections import Counter
import json
import random
import shutil
import sys
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from vision.brand.data_utils import (  # noqa: E402
    BoxXYXY,
    read_coco,
    read_voc,
    read_yolo,
    write_brands_yaml,
    write_yolo_label,
)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def _iter_images(root: Path) -> Iterator[Path]:
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            yield p


def _detect_format(src_root: Path) -> str:
    # COCO: any json containing images+annotations keys
    for js in src_root.rglob("*.json"):
        try:
            obj = json.loads(js.read_text(encoding="utf-8"))
            if isinstance(obj, dict) and "images" in obj and "annotations" in obj:
                return "coco"
        except Exception:
            continue

    # VOC: any xml
    if any(src_root.rglob("*.xml")):
        return "voc"

    # YOLO: labels/*.txt or annotations/*.txt or any directory named labels
    if any((src_root / "labels").rglob("*.txt")):
        return "yolo"
    if any(src_root.rglob("labels/*.txt")):
        return "yolo"
    if any(src_root.rglob("annotations/*.txt")):
        return "yolo"
    # Some datasets store image/label pairs in the same directory (e.g., train/*.jpg + train/*.txt)
    if any(src_root.rglob("*.txt")) and any(src_root.rglob("*.jpg")):
        return "yolo"

    # fallback guess
    return "unknown"


def _resolve_images_root(src_root: Path) -> Path:
    for cand in [src_root / "images", src_root / "Images", src_root]:
        if cand.exists():
            return cand
    return src_root


def _safe_rel_stem(p: Path) -> str:
    # stable unique key for image/label naming
    return "__".join(p.with_suffix("").parts[-3:])


def _copy_image(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(src, dst)
    except Exception:
        # ignore copy failures
        pass


def _image_size(img_path: Path) -> tuple[int, int] | None:
    try:
        from PIL import Image

        with Image.open(img_path) as im:
            return int(im.size[0]), int(im.size[1])
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Prepare a brand dataset into unified YOLO format (logo/car/fashion)."
    )
    ap.add_argument("--kind", type=str, choices=["logo", "car", "fashion"], default=None)
    # Keep backward compatibility with older docs that used "logodet3k".
    default_logo = (
        "data/raw/brand/LogoDet-3K"
        if Path("data/raw/brand/LogoDet-3K").exists()
        else "data/raw/brand/logodet3k"
    )
    ap.add_argument("--src_root", type=str, default=None)
    ap.add_argument("--out_root", type=str, default=None)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--val_ratio", type=float, default=0.1)
    args = ap.parse_args()

    kind = (args.kind or "").strip().lower()
    if kind:
        default_src = default_logo if kind == "logo" else f"data/raw/brand/{kind}"
        default_out = f"data/processed/brand_yolo/{kind}"
    else:
        default_src = default_logo
        default_out = "data/processed/brand_yolo"

    src_root = Path(args.src_root or default_src)
    out_root = Path(args.out_root or default_out)
    random.seed(int(args.seed))

    fmt = _detect_format(src_root)
    if fmt == "unknown":
        print(f"[prepare_brand_data] Could not auto-detect dataset format under: {src_root}")
        print("Expected COCO JSON, Pascal VOC XML, or YOLO labels/*.txt")
        return 2

    out_images_train = out_root / "images" / "train"
    out_images_val = out_root / "images" / "val"
    out_labels_train = out_root / "labels" / "train"
    out_labels_val = out_root / "labels" / "val"

    out_images_train.mkdir(parents=True, exist_ok=True)
    out_images_val.mkdir(parents=True, exist_ok=True)
    out_labels_train.mkdir(parents=True, exist_ok=True)
    out_labels_val.mkdir(parents=True, exist_ok=True)

    # Build a generator of (img_path, boxes)
    samples: list[tuple[Path, list[BoxXYXY]]] = []

    if fmt == "coco":
        images_root = _resolve_images_root(src_root)
        coco_jsons = []
        for js in src_root.rglob("*.json"):
            try:
                obj = json.loads(js.read_text(encoding="utf-8"))
                if isinstance(obj, dict) and "images" in obj and "annotations" in obj:
                    coco_jsons.append(js)
            except Exception:
                continue
        if not coco_jsons:
            print("[prepare_brand_data] No COCO JSON found after detection.")
            return 2
        # Use the first COCO json
        for img_path, boxes in read_coco(coco_jsons[0], images_root=images_root):
            if img_path.exists():
                samples.append((img_path, boxes))
            else:
                # try resolve relative to dataset
                alt = images_root / img_path.name
                if alt.exists():
                    samples.append((alt, boxes))
                else:
                    print(f"[warn] missing image: {img_path}")

    elif fmt == "voc":
        images_root = _resolve_images_root(src_root)
        for xml_path in src_root.rglob("*.xml"):
            img_rel, boxes = read_voc(xml_path)
            if img_rel is None:
                continue
            # Try in same folder, then images_root
            candidates = [
                xml_path.parent / img_rel,
                images_root / img_rel.name,
                images_root / img_rel,
            ]
            img_path = next((c for c in candidates if c.exists()), None)
            if img_path is None:
                print(f"[warn] missing VOC image for {xml_path}")
                continue
            samples.append((img_path, boxes))

    elif fmt == "yolo":
        # Expect labels/*.txt (or annotations/*.txt) and images/*
        labels_root = src_root / "labels"
        if not labels_root.exists():
            labels_root = next((p for p in src_root.rglob("labels") if p.is_dir()), labels_root)
        if not labels_root.exists():
            labels_root = next(
                (p for p in src_root.rglob("annotations") if p.is_dir()), labels_root
            )
        images_root = _resolve_images_root(src_root)

        # Try to load class names from dataset yaml if present
        class_names: list[str] = []
        for y in src_root.rglob("*.yaml"):
            try:
                import yaml

                obj = yaml.safe_load(y.read_text(encoding="utf-8"))
                names = obj.get("names") if isinstance(obj, dict) else None
                if isinstance(names, list) and names:
                    class_names = [str(n) for n in names]
                    break
            except Exception:
                continue

        # Gather label files. Prefer an explicit labels_root if it exists; otherwise
        # fall back to any txt files that appear to be paired with images.
        txt_files = list(labels_root.rglob("*.txt")) if labels_root.exists() else []
        if not txt_files:
            txt_files = [
                p
                for p in src_root.rglob("*.txt")
                if (
                    p.with_suffix(".jpg").exists()
                    or p.with_suffix(".jpeg").exists()
                    or p.with_suffix(".png").exists()
                )
            ]

        for txt in txt_files:
            stem = txt.stem
            # best-effort image match
            img_path = None
            for ext in IMAGE_EXTS:
                # If labels are beside images, this will hit.
                cand = images_root / f"{stem}{ext}"
                if cand.exists():
                    img_path = cand
                    break
            if img_path is None:
                # If label is in same folder as the image, try that.
                for ext in IMAGE_EXTS:
                    cand = txt.with_suffix(ext)
                    if cand.exists():
                        img_path = cand
                        break

            if img_path is None:
                # try any-image search
                for ext in IMAGE_EXTS:
                    cand = next((p for p in images_root.rglob(f"{stem}{ext}")), None)
                    if cand is not None:
                        img_path = cand
                        break
            if img_path is None:
                print(f"[warn] missing image for label: {txt}")
                continue

            if not class_names:
                # fallback: infer max cls id from file
                try:
                    ids = []
                    for line in txt.read_text(encoding="utf-8").splitlines():
                        parts = line.split()
                        if parts:
                            ids.append(int(float(parts[0])))
                    max_id = max(ids) if ids else -1
                    class_names = [str(i) for i in range(max_id + 1)]
                except Exception:
                    class_names = []

            samples.append(read_yolo(txt, img_path, class_names=class_names))

    if not samples:
        print("[prepare_brand_data] No samples collected (check dataset layout).")
        return 2

    # Build class list
    class_set = set()
    for _, boxes in samples:
        for b in boxes:
            class_set.add(str(b.cls_name))
    class_list = sorted(class_set)
    class_to_id = {c: i for i, c in enumerate(class_list)}

    # deterministic split
    indices = list(range(len(samples)))
    random.shuffle(indices)
    val_n = (
        max(1, int(len(indices) * float(args.val_ratio)))
        if len(indices) > 10
        else max(0, int(len(indices) * float(args.val_ratio)))
    )
    val_idx = set(indices[:val_n])

    brand_counts_train: Counter[str] = Counter()
    brand_counts_val: Counter[str] = Counter()
    total_imgs_train = 0
    total_imgs_val = 0
    total_boxes_train = 0
    total_boxes_val = 0

    for i, (img_path, boxes) in enumerate(samples):
        split = "val" if i in val_idx else "train"
        key = _safe_rel_stem(img_path)
        out_img = (
            out_images_val if split == "val" else out_images_train
        ) / f"{key}{img_path.suffix.lower()}"
        out_lbl = (out_labels_val if split == "val" else out_labels_train) / f"{key}.txt"

        if not img_path.exists():
            print(f"[warn] skip missing image: {img_path}")
            continue

        size = _image_size(img_path)
        if size is None:
            print(f"[warn] skip unreadable image: {img_path}")
            continue
        w, h = size

        _copy_image(img_path, out_img)
        write_yolo_label(out_lbl, boxes_xyxy=boxes, class_to_id=class_to_id, img_w=w, img_h=h)

        if split == "val":
            total_imgs_val += 1
            total_boxes_val += len(boxes)
            for b in boxes:
                brand_counts_val[str(b.cls_name)] += 1
        else:
            total_imgs_train += 1
            total_boxes_train += len(boxes)
            for b in boxes:
                brand_counts_train[str(b.cls_name)] += 1

    yaml_path = out_root / "brands.yaml"
    write_brands_yaml(
        yaml_path,
        train_images_dir=out_images_train,
        val_images_dir=out_images_val,
        class_list=class_list,
    )

    print("\n[prepare_brand_data] Done")
    print(f"format: {fmt}")
    print(f"classes: {len(class_list)}")
    print(f"train_images: {total_imgs_train}  train_boxes: {total_boxes_train}")
    print(f"val_images:   {total_imgs_val}  val_boxes:   {total_boxes_val}")

    print("\nTop brands (train):")
    for name, cnt in brand_counts_train.most_common(15):
        print(f"  {name}: {cnt}")

    print("\nTop brands (val):")
    for name, cnt in brand_counts_val.most_common(15):
        print(f"  {name}: {cnt}")

    print(f"\nYOLO dataset written to: {out_root}")
    print(f"Config: {yaml_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
