from __future__ import annotations

import json
import re
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from app.services.vision.yolov3 import detect_objects_yolov3, render_detections_yolov3
from app.utils.uploads import (
    IMAGE_EXTENSIONS,
    IMAGE_MIME_TYPES,
    MAX_IMAGE_BYTES,
    read_image_payload,
)

router = APIRouter(prefix="/api/vision/object", tags=["vision-object"])


def _parse_label_param(value: str | None) -> set[str]:
    if not value:
        return set()
    raw = value.strip()
    if not raw:
        return set()
    tokens: list[str] = []
    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            tokens = [str(item) for item in parsed]
        elif parsed is not None:
            tokens = [str(parsed)]
    if not tokens:
        tokens = re.split(r"[,\s]+", raw)
    return {tok.strip().lower() for tok in tokens if str(tok).strip()}


def _parse_id_param(value: str | None) -> set[int]:
    if not value:
        return set()
    raw = value.strip()
    if not raw:
        return set()
    tokens: list[str] = []
    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            tokens = [str(item) for item in parsed]
        elif parsed is not None:
            tokens = [str(parsed)]
    if not tokens:
        tokens = re.split(r"[,\s]+", raw)
    out: set[int] = set()
    for token in tokens:
        token = str(token).strip()
        if not token:
            continue
        try:
            out.add(int(token))
        except ValueError:
            continue
    return out


@router.post("/detect")
async def detect_objects(
    file: UploadFile | None = File(None),
    image_url: str | None = Form(default=None),
    image_base64: str | None = Form(default=None),
    conf: float | None = Form(default=None),
    nms: float | None = Form(default=None),
    top_k: int | None = Form(default=None),
    labels: str | None = Form(default=None),
    class_ids: str | None = Form(default=None),
) -> dict[str, Any]:
    try:
        image_bytes = await read_image_payload(
            file=file,
            image_url=image_url,
            image_base64=image_base64,
            allowed_exts=IMAGE_EXTENSIONS,
            allowed_mimes=IMAGE_MIME_TYPES,
            max_bytes=MAX_IMAGE_BYTES,
            kind="image",
        )
        allowed_labels = _parse_label_param(labels)
        allowed_ids = _parse_id_param(class_ids)
        payload = detect_objects_yolov3(
            image_bytes,
            conf=conf,
            nms=nms,
            top_k=top_k,
            allowed_labels=allowed_labels or None,
            allowed_ids=allowed_ids or None,
        )
        return payload
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Object detection failed: {exc}") from exc


@router.post("/visualize")
async def visualize_objects(
    file: UploadFile | None = File(None),
    image_url: str | None = Form(default=None),
    image_base64: str | None = Form(default=None),
    conf: float | None = Form(default=None),
    nms: float | None = Form(default=None),
    top_k: int | None = Form(default=None),
    labels: str | None = Form(default=None),
    class_ids: str | None = Form(default=None),
) -> Response:
    try:
        image_bytes = await read_image_payload(
            file=file,
            image_url=image_url,
            image_base64=image_base64,
            allowed_exts=IMAGE_EXTENSIONS,
            allowed_mimes=IMAGE_MIME_TYPES,
            max_bytes=MAX_IMAGE_BYTES,
            kind="image",
        )
        allowed_labels = _parse_label_param(labels)
        allowed_ids = _parse_id_param(class_ids)
        payload = detect_objects_yolov3(
            image_bytes,
            conf=conf,
            nms=nms,
            top_k=top_k,
            allowed_labels=allowed_labels or None,
            allowed_ids=allowed_ids or None,
        )
        annotated = render_detections_yolov3(image_bytes, payload["detections"])
        return Response(content=annotated, media_type="image/png")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Object visualization failed: {exc}") from exc
