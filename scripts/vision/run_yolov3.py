from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from app.services.vision.yolov3 import detect_objects_yolov3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run YOLOv3 object detection on a local image.")
    parser.add_argument("image", type=Path, help="Path to image file.")
    parser.add_argument("--conf", type=float, default=None, help="Confidence threshold.")
    parser.add_argument("--nms", type=float, default=None, help="NMS threshold.")
    parser.add_argument("--top-k", type=int, default=None, help="Max detections.")
    parser.add_argument(
        "--labels", type=str, default=None, help="Comma/space-separated COCO labels."
    )
    parser.add_argument(
        "--class-ids", type=str, default=None, help="Comma/space-separated class ids."
    )
    parser.add_argument("--out", type=Path, default=None, help="Output JSON path.")
    return parser.parse_args()


def _parse_labels(value: str | None) -> set[str]:
    if not value:
        return set()
    tokens = re.split(r"[,\s]+", value.strip())
    return {tok.strip().lower() for tok in tokens if tok.strip()}


def _parse_ids(value: str | None) -> set[int]:
    if not value:
        return set()
    tokens = re.split(r"[,\s]+", value.strip())
    out: set[int] = set()
    for token in tokens:
        if not token:
            continue
        try:
            out.add(int(token))
        except ValueError:
            continue
    return out


def main() -> None:
    args = parse_args()
    if not args.image.exists():
        raise SystemExit(f"Image not found: {args.image}")
    image_bytes = args.image.read_bytes()
    allowed_labels = _parse_labels(args.labels)
    allowed_ids = _parse_ids(args.class_ids)
    payload = detect_objects_yolov3(
        image_bytes,
        conf=args.conf,
        nms=args.nms,
        top_k=args.top_k,
        allowed_labels=allowed_labels or None,
        allowed_ids=allowed_ids or None,
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"[yolov3] wrote {args.out}")
    else:
        print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
