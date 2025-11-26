from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/recommend", tags=["recommend"])


class RecommendRequest(BaseModel):
    query: str


@router.post("")
def recommend(req: RecommendRequest):
    # Placeholder: call recommender and return suggestions
    return {"items": [], "message": "Recommender endpoint not wired yet", "query": req.query}
