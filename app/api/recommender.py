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
) -> dict[str, object]:
    """Multimodal recommendations via CLIP similarity search.

    This is additive and doesn't replace the existing recommender.
    Provide either:
    - image upload, or
    - text query
    """
    try:
        image_bytes = await image.read() if image is not None else None
        return predict_multimodal(text=text, image_bytes=image_bytes, top_k=top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
