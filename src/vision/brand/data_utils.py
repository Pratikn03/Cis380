from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict, Iterator, Sequence


@dataclass(frozen=True)
class BoxXYXY:
    cls_name: str
    x1: float
    y1: float
    x2: float
    y2: float


def read_coco(coco_json_path: Path, images_root: Path) -> Iterator[tuple[Path, list[BoxXYXY]]]:
    """Read COCO detection annotations.

    Yields (img_path, boxes).
    Expects a standard COCO JSON with keys: images, annotations, categories.
    """
    data = json.loads(coco_json_path.read_text(encoding="utf-8"))

    cat_id_to_name: dict[int, str] = {}
    for c in data.get("categories", []) or []:
        try:
            cat_id_to_name[int(c["id"])] = str(
                c.get("name") or c.get("category") or c.get("label") or c["id"]
            )
        except Exception:
            continue

    img_id_to_path: dict[int, Path] = {}
    for img in data.get("images", []) or []:
        try:
            img_id = int(img["id"])
            file_name = img.get("file_name") or img.get("path") or img.get("name")
            if not file_name:
                continue
            img_id_to_path[img_id] = (images_root / str(file_name)).resolve()
        except Exception:
            continue

    img_id_to_boxes: dict[int, list[BoxXYXY]] = {k: [] for k in img_id_to_path.keys()}
    for ann in data.get("annotations", []) or []:
        try:
            img_id = int(ann["image_id"])
            cat_id = int(ann["category_id"])
            bbox = ann.get("bbox")
            if not bbox or len(bbox) != 4:
                continue
            x, y, w, h = bbox
            cls_name = cat_id_to_name.get(cat_id, str(cat_id))
            img_id_to_boxes.setdefault(img_id, []).append(
                BoxXYXY(
                    cls_name=cls_name, x1=float(x), y1=float(y), x2=float(x + w), y2=float(y + h)
                )
            )
        except Exception:
            continue

    for img_id, img_path in img_id_to_path.items():
        yield img_path, img_id_to_boxes.get(img_id, [])


def read_voc(xml_path: Path) -> tuple[Path | None, list[BoxXYXY]]:
    """Read a Pascal VOC XML file.

    Returns (img_path_or_none, boxes)
    """
    try:
        import xml.etree.ElementTree as ET

        root = ET.fromstring(xml_path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None, []

    filename = None
    fn = root.findtext("filename")
    if fn:
        filename = fn
    path_text = root.findtext("path")
    img_path = Path(path_text) if path_text else (Path(filename) if filename else None)

    boxes: list[BoxXYXY] = []
    for obj in root.findall("object"):
        name = obj.findtext("name")
        if not name:
            continue
        bnd = obj.find("bndbox")
        if bnd is None:
            continue
        try:
            x1 = float(bnd.findtext("xmin") or 0)
            y1 = float(bnd.findtext("ymin") or 0)
            x2 = float(bnd.findtext("xmax") or 0)
            y2 = float(bnd.findtext("ymax") or 0)
        except Exception:
            continue
        boxes.append(BoxXYXY(cls_name=str(name), x1=x1, y1=y1, x2=x2, y2=y2))

    return img_path, boxes


def read_yolo(
    label_txt_path: Path, img_path: Path, class_names: Sequence[str]
) -> tuple[Path, list[BoxXYXY]]:
    """Read a YOLO label txt file for a known image.

    label format: cls_id cx cy w h (normalized)
    Returns boxes in absolute pixel space (xyxy).
    """
    try:
        from PIL import Image

        with Image.open(img_path) as im:
            w, h = im.size
    except Exception:
        return img_path, []

    boxes: list[BoxXYXY] = []
    try:
        lines = label_txt_path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return img_path, []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        try:
            cls_id = int(float(parts[0]))
            cx, cy, bw, bh = map(float, parts[1:5])
        except Exception:
            continue
        if cls_id < 0 or cls_id >= len(class_names):
            cls_name = str(cls_id)
        else:
            cls_name = class_names[cls_id]
        x1 = (cx - bw / 2) * w
        y1 = (cy - bh / 2) * h
        x2 = (cx + bw / 2) * w
        y2 = (cy + bh / 2) * h
        boxes.append(
            BoxXYXY(cls_name=str(cls_name), x1=float(x1), y1=float(y1), x2=float(x2), y2=float(y2))
        )

    return img_path, boxes


def write_yolo_label(
    label_path: Path,
    boxes_xyxy: Sequence[BoxXYXY],
    class_to_id: Dict[str, int],
    img_w: int,
    img_h: int,
) -> None:
    """Write YOLO labels in normalized cxcywh format."""
    lines: list[str] = []
    for b in boxes_xyxy:
        if b.cls_name not in class_to_id:
            continue
        # clip
        x1 = max(0.0, min(float(img_w), float(b.x1)))
        y1 = max(0.0, min(float(img_h), float(b.y1)))
        x2 = max(0.0, min(float(img_w), float(b.x2)))
        y2 = max(0.0, min(float(img_h), float(b.y2)))
        if x2 <= x1 or y2 <= y1:
            continue
        cx = (x1 + x2) / 2.0 / img_w
        cy = (y1 + y2) / 2.0 / img_h
        bw = (x2 - x1) / img_w
        bh = (y2 - y1) / img_h
        cls_id = class_to_id[b.cls_name]
        lines.append(f"{cls_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")

    label_path.parent.mkdir(parents=True, exist_ok=True)
    label_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_brands_yaml(
    out_yaml_path: Path, train_images_dir: Path, val_images_dir: Path, class_list: Sequence[str]
) -> None:
    """Write ultralytics dataset yaml."""
    dataset_root = out_yaml_path.parent.resolve()

    def _find_project_root(path: Path) -> Path | None:
        for parent in (path, *path.parents):
            if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
                return parent
        return None

    def _relative_to(path: Path, root: Path) -> str:
        try:
            return path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            return str(path.resolve())

    project_root = _find_project_root(dataset_root)
    dataset_path = (
        _relative_to(dataset_root, project_root) if project_root is not None else str(dataset_root)
    )

    payload = {
        "path": dataset_path,
        "train": _relative_to(train_images_dir, dataset_root),
        "val": _relative_to(val_images_dir, dataset_root),
        "names": list(class_list),
    }
    out_yaml_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import yaml

        out_yaml_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    except Exception:
        # Fallback to a minimal YAML-like writer (should still be parseable)
        lines = [
            f"path: {payload['path']}",
            f"train: {payload['train']}",
            f"val: {payload['val']}",
            "names:",
        ]
        for name in payload["names"]:
            lines.append(f"  - {name}")
        out_yaml_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


__all__ = [
    "BoxXYXY",
    "read_coco",
    "read_voc",
    "read_yolo",
    "write_yolo_label",
    "write_brands_yaml",
]
