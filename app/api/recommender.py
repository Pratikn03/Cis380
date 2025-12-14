from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.models.recommender.explain import explain_recommendation
from app.models.recommender.predict import recommend

router = APIRouter()


class RecommendRequest(BaseModel):
    user_id: str = "anon"
    top_k: Optional[int] = Field(default=5, ge=1, le=20)


class ExplainRequest(BaseModel):
    user_id: str = "anon"
    item_id: str


@router.post("/recommend")
async def recommend_items(payload: RecommendRequest) -> dict[str, object]:
    items = recommend(payload.user_id, payload.top_k)
    return {"items": items}


@router.post("/recommend/explain")
async def explain_item(payload: ExplainRequest) -> dict[str, str]:
    explanation = explain_recommendation(payload.user_id, payload.item_id)
    return {"explanation": explanation}
