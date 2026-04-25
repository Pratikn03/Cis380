from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.utils.uploads import (
    IMAGE_EXTENSIONS,
    IMAGE_MIME_TYPES,
    MAX_IMAGE_BYTES,
    read_image_payload,
)

router = APIRouter()

_mm_backend = None
_mm_backend_loaded = False


def _get_multimodal_backend():
    global _mm_backend, _mm_backend_loaded

    if _mm_backend_loaded:
        return _mm_backend
    _mm_backend_loaded = True
    try:  # pragma: no cover - optional CLIP/FAISS backend
        from app.models.recommender.multimodal import multimodal_predict

        _mm_backend = multimodal_predict
    except Exception:  # pragma: no cover
        _mm_backend = None
    return _mm_backend


class RecommendRequest(BaseModel):
    user_id: str = "anon"
    top_k: Optional[int] = Field(default=5, ge=1, le=20)


class ExplainRequest(BaseModel):
    user_id: str = "anon"
    item_id: str


@router.post("/recommend")
async def recommend_items(payload: RecommendRequest) -> dict[str, object]:
    from app.models.recommender.predict import recommend

    items = recommend(payload.user_id, payload.top_k or 5)
    return {"items": items}


@router.post("/recommend/explain")
async def explain_item(payload: ExplainRequest) -> dict[str, str]:
    from app.models.recommender.explain import explain_recommendation

    explanation = explain_recommendation(payload.user_id, payload.item_id)
    return {"explanation": explanation}


@router.post("/recommend/multimodal")
async def recommend_multimodal(
    text: Optional[str] = Form(default=None),
    top_k: int = Form(default=5, ge=1, le=20),
    image: UploadFile | None = File(default=None),
    image_url: str | None = Form(default=None),
    image_base64: str | None = Form(default=None),
    use_brand: bool = Form(default=False),
    brand_kind: str = Form(default="logo"),
    use_objects: bool = Form(default=True),
) -> dict[str, object]:
    """Multimodal recommendations via CLIP similarity search.

    This is additive and doesn't replace the existing recommender.
    Provide either:
    - image upload, or
    - image_url / image_base64, or
    - text query
    """
    try:
        image_bytes = None
        if image is not None or image_url or image_base64:
            image_bytes = await read_image_payload(
                file=image,
                image_url=image_url,
                image_base64=image_base64,
                allowed_exts=IMAGE_EXTENSIONS,
                allowed_mimes=IMAGE_MIME_TYPES,
                max_bytes=MAX_IMAGE_BYTES,
                kind="image",
            )
        brand_detections = None
        brand_error = None
        brand_model = None

        text_value = text

        # 1. Generic Object Detection (YOLO)
        # Identifies the "what" (e.g., "shoe", "bag", "car")
        if use_objects and image_bytes is not None:
            try:
                from app.services.vision.yolov3 import detect_objects_yolov3

                yolo_out = await run_in_threadpool(
                    detect_objects_yolov3, image_bytes, conf=0.3, top_k=5
                )
                detections = yolo_out.get("detections", [])
                labels = {d["label"] for d in detections if d.get("label")}
                if labels:
                    labels_str = " ".join(sorted(labels))
                    text_value = f"{text_value} {labels_str}" if text_value else labels_str
            except Exception:
                pass  # Continue if object detection fails

        # 2. Brand Recognition
        # Identifies the "who" (e.g., "Nike", "Gucci")
        if use_brand and image_bytes is not None:
            try:
                from src.vision.brand.recognizer import model_path, predict_image_bytes

                brand_detections = predict_image_bytes(image_bytes, conf=0.25, kind=brand_kind)
                brand_model = model_path(kind=brand_kind)
                if brand_detections:
                    top_brand = brand_detections[0].get("brand")
                    if top_brand:
                        if text_value:
                            text_value = f"{text_value} brand {top_brand}"
                        else:
                            text_value = str(top_brand)
            except Exception as exc:
                brand_error = str(exc)

        mm_backend = _get_multimodal_backend()
        if mm_backend is not None:
            try:
                result = mm_backend.multimodal_recommend(
                    text=text_value,
                    image_bytes=image_bytes,
                    top_k=top_k,
                )
            except Exception as exc:
                if isinstance(exc, mm_backend.IndexNotBuiltError):
                    raise HTTPException(status_code=503, detail=str(exc)) from exc
                raise
        else:
            from app.models.recommender.predict import predict_multimodal

            result = predict_multimodal(text=text_value, image_bytes=image_bytes, top_k=top_k)
        if use_brand:
            result["brand_detections"] = brand_detections
            result["brand_model"] = brand_model
            result["brand_kind"] = brand_kind
            result["brand_error"] = brand_error
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/recommend/clothes")
async def recommend_clothes(
    text: Optional[str] = Form(default=None),
    top_k: int = Form(default=5, ge=1, le=20),
    image: UploadFile | None = File(default=None),
    image_url: str | None = Form(default=None),
    image_base64: str | None = Form(default=None),
) -> dict[str, object]:
    query = (text or "").strip()
    image_tags: list[str] = []
    tag_error: str | None = None
    image_bytes = None

    if image is not None or image_url or image_base64:
        try:
            import io

            from PIL import Image

            from app.streamlit_chatbot.image_tags import extract_tags_from_image

            image_bytes = await read_image_payload(
                file=image,
                image_url=image_url,
                image_base64=image_base64,
                allowed_exts=IMAGE_EXTENSIONS,
                allowed_mimes=IMAGE_MIME_TYPES,
                max_bytes=MAX_IMAGE_BYTES,
                kind="image",
            )
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            image_tags = extract_tags_from_image(img, top_k=5)
        except Exception as exc:
            tag_error = str(exc)

    if not query and image_bytes is None:
        raise HTTPException(status_code=400, detail="Provide a text prompt or an image.")

    try:
        from app.streamlit_chatbot.handlers.clothes import recommend_clothes as _recommend_clothes

        items = _recommend_clothes(
            age=None,
            query=query,
            preferred_tags=image_tags,
            top_k=top_k,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Clothing recommendation failed: {exc}"
        ) from exc

    payload: dict[str, object] = {
        "mode": "clothes",
        "query": query,
        "image_tags": image_tags,
        "items": items,
    }
    if tag_error:
        payload["image_tag_error"] = tag_error
        if not image_tags:
            payload["notice"] = "Image tags unavailable; using text-only recommendation inputs."
    return payload
