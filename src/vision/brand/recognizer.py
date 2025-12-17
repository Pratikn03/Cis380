from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, List


_ARTIFACT_PATH = Path("artifacts/brand/yolo_logo_det.pt")
_MODEL = None
_MODEL_ERROR: str | None = None


def _get_model():
    global _MODEL, _MODEL_ERROR
    if _MODEL is not None:
        return _MODEL
    if _MODEL_ERROR is not None:
        raise RuntimeError(_MODEL_ERROR)

    if not _ARTIFACT_PATH.exists():
        _MODEL_ERROR = (
            "Brand model not trained. Run scripts/prepare_brand_data.py then "
            "python -m src.train.train_brand_logo_detector to create artifacts/brand/yolo_logo_det.pt"
        )
        raise RuntimeError(_MODEL_ERROR)

    try:
        from ultralytics import YOLO
    except Exception as exc:
        _MODEL_ERROR = f"ultralytics not available: {exc}"
        raise RuntimeError(_MODEL_ERROR) from exc

    try:
        _MODEL = YOLO(str(_ARTIFACT_PATH))
    except Exception as exc:
        _MODEL_ERROR = f"Could not load YOLO weights at {_ARTIFACT_PATH}: {exc}"
        raise RuntimeError(_MODEL_ERROR) from exc

    return _MODEL


def predict_image_bytes(image_bytes: bytes, *, conf: float = 0.25) -> List[Dict[str, Any]]:
    """Return logo detections with brand names and bounding boxes."""
    model = _get_model()

    # Ultralytics accepts np arrays, PIL images, and file paths. We'll use PIL to avoid temp files.
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as exc:
        raise ValueError(f"Invalid image bytes: {exc}") from exc

    results = model.predict(img, conf=conf, verbose=False)
    if not results:
        return []

    r0 = results[0]
    names = getattr(r0, "names", None) or {}

    detections: list[dict[str, Any]] = []
    boxes = getattr(r0, "boxes", None)
    if boxes is None:
        return []

    xyxy = getattr(boxes, "xyxy", None)
    cls = getattr(boxes, "cls", None)
    confs = getattr(boxes, "conf", None)
    if xyxy is None or cls is None or confs is None:
        return []

    # Convert tensors to python lists
    try:
        xyxy_list = xyxy.detach().cpu().tolist()
        cls_list = cls.detach().cpu().tolist()
        conf_list = confs.detach().cpu().tolist()
    except Exception:
        xyxy_list = list(xyxy)
        cls_list = list(cls)
        conf_list = list(confs)

    for (x1, y1, x2, y2), c, p in zip(xyxy_list, cls_list, conf_list):
        try:
            cid = int(c)
        except Exception:
            cid = 0
        brand = names.get(cid, str(cid))
        detections.append(
            {
                "brand": str(brand),
                "confidence": float(p),
                "bbox": [float(x1), float(y1), float(x2), float(y2)],
            }
        )

    return detections


def model_path() -> str:
    return str(_ARTIFACT_PATH)


__all__ = ["predict_image_bytes", "model_path"]
