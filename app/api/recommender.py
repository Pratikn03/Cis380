from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.models.recommender.explain import explain_recommendation
from app.models.recommender.predict import predict_multimodal, recommend

router = APIRouter()


class RecommendRequest(BaseModel):
    user_id: str = "anon"
    top_k: Optional[int] = Field(default=5, ge=1, le=20)


class ExplainRequest(BaseModel):
    user_id: str = "anon"
    item_id: str


@router.post("/recommend")
async def recommend_items(payload: RecommendRequest) -> dict[str, object]:
    items = recommend(payload.user_id, payload.top_k or 5)
    return {"items": items}


@router.post("/recommend/explain")
async def explain_item(payload: ExplainRequest) -> dict[str, str]:
    explanation = explain_recommendation(payload.user_id, payload.item_id)
    return {"explanation": explanation}


@router.post("/recommend/multimodal")
async def recommend_multimodal(
    text: Optional[str] = Form(default=None),
    top_k: int = Form(default=5, ge=1, le=20),
    image: UploadFile | None = File(default=None),
    use_brand: bool = Form(default=False),
    brand_kind: str = Form(default="logo"),
) -> dict[str, object]:
    """Multimodal recommendations via CLIP similarity search.

    This is additive and doesn't replace the existing recommender.
    Provide either:
    - image upload, or
    - text query
    """
    try:
        image_bytes = await image.read() if image is not None else None
        brand_detections = None
        brand_error = None
        brand_model = None

        text_value = text
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

        result = predict_multimodal(text=text_value, image_bytes=image_bytes, top_k=top_k)
        if use_brand:
            result["brand_detections"] = brand_detections
            result["brand_model"] = brand_model
            result["brand_kind"] = brand_kind
            result["brand_error"] = brand_error
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
