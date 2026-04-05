from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Any, Dict, List

_MODEL_CACHE: dict[str, object] = {}
_MODEL_ERROR: dict[str, str] = {}


def _normalize_kind(kind: str | None) -> str:
    return (kind or "logo").strip().lower() or "logo"


def _model_registry() -> dict[str, Path]:
    default_logo = Path("artifacts/brand/yolo_logo_det.pt")
    logo_path = os.getenv("BRAND_MODEL_LOGO_PATH")

    # Fallback: If default artifact missing, check for local training run
    if not logo_path and not default_logo.exists():
        local_run = Path("runs/detect/train/weights/best.pt")
        if local_run.exists():
            default_logo = local_run

    if not logo_path:
        logo_path = os.getenv("BRAND_MODEL_PATH", str(default_logo))
    return {
        "logo": Path(logo_path),
        "car": Path(os.getenv("BRAND_MODEL_CAR_PATH", "artifacts/brand/yolo_car_brand.pt")),
        "fashion": Path(
            os.getenv("BRAND_MODEL_FASHION_PATH", "artifacts/brand/yolo_fashion_brand.pt")
        ),
    }


def available_model_kinds(*, include_missing: bool = False) -> dict[str, str]:
    registry = _model_registry()
    if include_missing:
        return {k: str(v) for k, v in registry.items()}
    return {k: str(v) for k, v in registry.items() if v.exists()}


def _resolve_model_path(kind: str | None) -> Path:
    key = _normalize_kind(kind)
    registry = _model_registry()
    return registry.get(key, registry["logo"])


def _get_model(kind: str | None):
    key = _normalize_kind(kind)
    model_path = _resolve_model_path(key)
    cache_key = f"{key}:{model_path}"
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]
    if cache_key in _MODEL_ERROR:
        raise RuntimeError(_MODEL_ERROR[cache_key])

    if not model_path.exists():
        msg = (
            f"Brand model not trained for kind='{key}'. "
            f"Expected weights at {model_path}. "
            "Run scripts/prepare_brand_data.py --kind <logo|car|fashion> then "
            "python -m src.train.train_brand_logo_detector to create the artifact."
        )
        _MODEL_ERROR[cache_key] = msg
        raise RuntimeError(msg)

    try:
        from ultralytics import YOLO
    except Exception as exc:
        msg = f"ultralytics not available: {exc}"
        _MODEL_ERROR[cache_key] = msg
        raise RuntimeError(msg) from exc

    try:
        model = YOLO(str(model_path))
    except Exception as exc:
        msg = f"Could not load YOLO weights at {model_path}: {exc}"
        _MODEL_ERROR[cache_key] = msg
        raise RuntimeError(msg) from exc

    _MODEL_CACHE[cache_key] = model
    return model


def predict_image_bytes(
    image_bytes: bytes,
    *,
    conf: float = 0.25,
    kind: str | None = None,
) -> List[Dict[str, Any]]:
    """Return logo detections with brand names and bounding boxes."""
    model = _get_model(kind)

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


def model_path(kind: str | None = None) -> str:
    return str(_resolve_model_path(kind))


__all__ = ["predict_image_bytes", "model_path", "available_model_kinds"]
