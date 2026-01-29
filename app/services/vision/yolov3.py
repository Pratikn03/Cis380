from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any
import re

import numpy as np

try:
    import cv2  # type: ignore
except Exception as exc:  # pragma: no cover - optional dependency
    cv2 = None
    _cv2_error = exc
else:
    _cv2_error = None


DEFAULT_ROOT = Path("artifacts/vision/yolov3")
DEFAULT_CFG = DEFAULT_ROOT / "yolov3.cfg"
DEFAULT_WEIGHTS = DEFAULT_ROOT / "yolov3.weights"
DEFAULT_NAMES = DEFAULT_ROOT / "coco.names"


def _get_paths() -> tuple[Path, Path, Path]:
    cfg = Path(os.getenv("YOLOV3_CFG", DEFAULT_CFG))
    weights = Path(os.getenv("YOLOV3_WEIGHTS", DEFAULT_WEIGHTS))
    names = Path(os.getenv("YOLOV3_NAMES", DEFAULT_NAMES))
    return cfg, weights, names


def _parse_label_list(value: str | None) -> set[str]:
    if not value:
        return set()
    tokens = re.split(r"[,\s]+", value.strip())
    return {tok.strip().lower() for tok in tokens if tok.strip()}


def _parse_id_list(value: str | None) -> set[int]:
    if not value:
        return set()
    out = set()
    for part in re.split(r"[,\s]+", value.strip()):
        if not part:
            continue
        try:
            out.add(int(part))
        except ValueError:
            continue
    return out


def _require_cv2() -> None:
    if cv2 is None:
        raise RuntimeError(
            "opencv-python is required for YOLOv3 inference. Install it via "
            "`pip install opencv-python` (or opencv-python-headless)."
        ) from _cv2_error


@lru_cache(maxsize=1)
def _load_names(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Missing YOLOv3 class names: {path}")
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


@lru_cache(maxsize=1)
def _load_net(cfg: str, weights: str) -> Any:
    _require_cv2()
    cfg_path = Path(cfg)
    weights_path = Path(weights)
    if not cfg_path.exists():
        raise FileNotFoundError(f"Missing YOLOv3 config: {cfg_path}")
    if not weights_path.exists():
        raise FileNotFoundError(f"Missing YOLOv3 weights: {weights_path}")
    net = cv2.dnn.readNetFromDarknet(str(cfg_path), str(weights_path))

    backend = (os.getenv("YOLOV3_BACKEND") or "opencv").lower()
    target = (os.getenv("YOLOV3_TARGET") or "cpu").lower()

    if backend == "cuda" and hasattr(cv2.dnn, "DNN_BACKEND_CUDA"):
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
    else:
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)

    if target == "cuda" and hasattr(cv2.dnn, "DNN_TARGET_CUDA"):
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
    else:
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    return net


def _output_layer_names(net: Any) -> list[str]:
    try:
        return net.getUnconnectedOutLayersNames()  # OpenCV >= 4.2
    except Exception:
        layer_names = net.getLayerNames()
        return [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]


def detect_objects_yolov3(
    image_bytes: bytes,
    *,
    conf: float | None = None,
    nms: float | None = None,
    top_k: int | None = None,
    allowed_labels: set[str] | None = None,
    allowed_ids: set[int] | None = None,
) -> dict[str, Any]:
    _require_cv2()
    cfg, weights, names_path = _get_paths()
    labels = _load_names(names_path)
    net = _load_net(str(cfg), str(weights))

    img_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Invalid image bytes or unsupported image format.")

    height, width = image.shape[:2]
    input_size = int(os.getenv("YOLOV3_INPUT_SIZE", "416"))
    conf_th = float(os.getenv("YOLOV3_CONFIDENCE", "0.5")) if conf is None else float(conf)
    nms_th = float(os.getenv("YOLOV3_NMS", "0.4")) if nms is None else float(nms)
    max_det = int(os.getenv("YOLOV3_MAX_DETECTIONS", "50")) if top_k is None else int(top_k)

    env_labels = _parse_label_list(os.getenv("YOLOV3_ALLOWED_CLASSES"))
    env_ids = _parse_id_list(os.getenv("YOLOV3_ALLOWED_IDS"))
    req_labels = {label.lower() for label in allowed_labels} if allowed_labels else set()
    req_ids = set(allowed_ids) if allowed_ids else set()

    if env_labels:
        effective_labels = env_labels & req_labels if req_labels else env_labels
    else:
        effective_labels = req_labels

    if env_ids:
        effective_ids = env_ids & req_ids if req_ids else env_ids
    else:
        effective_ids = req_ids

    blob = cv2.dnn.blobFromImage(
        image, 1 / 255.0, (input_size, input_size), swapRB=True, crop=False
    )
    net.setInput(blob)
    outputs = net.forward(_output_layer_names(net))

    boxes: list[list[int]] = []
    confidences: list[float] = []
    class_ids: list[int] = []

    for output in outputs:
        for detection in output:
            scores = detection[5:]
            class_id = int(np.argmax(scores))
            score = float(scores[class_id])
            objectness = float(detection[4])
            confidence = objectness * score
            if confidence < conf_th:
                continue
            center_x = int(detection[0] * width)
            center_y = int(detection[1] * height)
            box_w = int(detection[2] * width)
            box_h = int(detection[3] * height)
            x = int(center_x - box_w / 2)
            y = int(center_y - box_h / 2)
            boxes.append([x, y, box_w, box_h])
            confidences.append(confidence)
            class_ids.append(class_id)

    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_th, nms_th)
    detections: list[dict[str, Any]] = []
    if len(indices) > 0:
        for idx in indices.flatten().tolist():
            class_id = int(class_ids[idx])
            label = labels[class_id] if class_id < len(labels) else str(class_id)
            if effective_labels and label.lower() not in effective_labels:
                continue
            if effective_ids and class_id not in effective_ids:
                continue
            x, y, w, h = boxes[idx]
            detections.append(
                {
                    "label": label,
                    "class_id": class_id,
                    "confidence": float(confidences[idx]),
                    "box": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
                }
            )

    detections = sorted(detections, key=lambda d: d["confidence"], reverse=True)[:max_det]

    return {
        "model": "yolov3",
        "detections": detections,
        "count": len(detections),
        "image_size": {"width": width, "height": height},
        "filters": {
            "allowed_labels": sorted(effective_labels) if effective_labels else [],
            "allowed_ids": sorted(effective_ids) if effective_ids else [],
        },
    }


def render_detections_yolov3(
    image_bytes: bytes,
    detections: list[dict[str, Any]],
    *,
    color: tuple[int, int, int] | None = None,
    thickness: int = 2,
    font_scale: float = 0.5,
) -> bytes:
    _require_cv2()
    img_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Invalid image bytes or unsupported image format.")

    box_color = color or (0, 255, 0)
    for det in detections:
        box = det.get("box") or {}
        x = int(box.get("x", 0))
        y = int(box.get("y", 0))
        w = int(box.get("w", 0))
        h = int(box.get("h", 0))
        label = det.get("label", "object")
        conf = det.get("confidence", 0.0)
        cv2.rectangle(image, (x, y), (x + w, y + h), box_color, thickness)
        text = f"{label} {conf:.2f}"
        cv2.putText(
            image,
            text,
            (x, max(0, y - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            box_color,
            1,
            cv2.LINE_AA,
        )

    success, buffer = cv2.imencode(".png", image)
    if not success:
        raise RuntimeError("Failed to encode annotated image.")
    return buffer.tobytes()
