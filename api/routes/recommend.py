from pathlib import Path
from typing import List, Optional

import joblib
import numpy as np
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from api.deps import require_auth

router = APIRouter(prefix="/api/recommend", tags=["recommend"], dependencies=[Depends(require_auth)])


class RecommendRequest(BaseModel):
    # Option A: MovieLens-style
    user_id: Optional[int] = None
    movie_id: Optional[int] = None
    # Option B: generic numeric vector (backward compatible)
    features: Optional[List[float]] = None
    candidate_ids: Optional[List[int]] = None  # for top-N from a provided set


PROJECT_ROOT = Path(__file__).resolve().parents[2]

# generic/tabular recommender (XGBoost)
_rec_path = PROJECT_ROOT / "recommender" / "models" / "recommender.pkl"
_rec_model = joblib.load(_rec_path) if _rec_path.exists() else None

# MovieLens model/meta (uses same xgboost by default)
_ml_model_path = PROJECT_ROOT / "recommender" / "models" / "recommender.pkl"
_ml_meta_path = PROJECT_ROOT / "recommender" / "models" / "recommender_meta.joblib"
_ml_model = joblib.load(_ml_model_path) if _ml_model_path.exists() else None
_ml_meta = joblib.load(_ml_meta_path) if _ml_meta_path.exists() else None


def _ml_features(user_id: int, movie_id: int):
    if _ml_meta is None:
        return None
    user_stats = _ml_meta.get("user_stats")
    item_stats = _ml_meta.get("item_stats")
    global_mean = _ml_meta.get("global_mean", 3.5)
    user_codes = _ml_meta.get("user_codes", {})
    item_codes = _ml_meta.get("item_codes", {})
    feat_names = _ml_meta.get("feature_names", [])

    u_mean = user_stats.loc[user_id]["user_mean"] if user_id in user_stats.index else global_mean
    u_count = user_stats.loc[user_id]["user_count"] if user_id in user_stats.index else 0.0
    i_mean = item_stats.loc[movie_id]["item_mean"] if movie_id in item_stats.index else global_mean
    i_count = item_stats.loc[movie_id]["item_count"] if movie_id in item_stats.index else 0.0
    u_code = user_codes.get(user_id, 0)
    i_code = item_codes.get(movie_id, 0)

    values = {
        "user_mean": u_mean,
        "item_mean": i_mean,
        "user_count": u_count,
        "item_count": i_count,
        "global_mean": global_mean,
        "user_code": u_code,
        "item_code": i_code,
    }
    return np.array([[values.get(k, 0.0) for k in feat_names]]), feat_names


@router.post("")
def recommend(req: RecommendRequest):
    # Path A: MovieLens-style if user_id and movie_id provided and model exists
    if req.user_id is not None and req.movie_id is not None and _ml_model is not None:
        try:
            feats, names = _ml_features(req.user_id, req.movie_id)
            if feats is None:
                raise ValueError("MovieLens metadata not available.")
            proba = _ml_model.predict_proba(feats)[0]
            classes = list(getattr(_ml_model, "classes_", []))
            top_idx = int(np.argmax(proba))
            return {
                "mode": "movielens",
                "user_id": req.user_id,
                "movie_id": req.movie_id,
                "label": classes[top_idx] if classes else "like",
                "probability": float(proba[top_idx]),
                "feature_names": names,
            }
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"MovieLens recommendation failed: {exc}",
            )

    # Path B: generic vector fallback
    if _rec_model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Recommender model not found."
        )
    feats = req.features or []
    try:
        n = getattr(_rec_model, "n_features_in_", 0)
        arr = np.zeros((1, n), dtype=float)
        for i, v in enumerate(feats[:n]):
            arr[0, i] = v
        if hasattr(_rec_model, "predict_proba"):
            proba = _rec_model.predict_proba(arr)[0]
            classes = list(getattr(_rec_model, "classes_", []))
            top_idx = int(np.argmax(proba))
            result = {"label": classes[top_idx] if classes else "item", "probability": float(proba[top_idx])}
        else:
            label = _rec_model.predict(arr)[0]
            result = {"label": str(label), "probability": None}
        return {"mode": "generic", "input_filled": len(feats), "result": result}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation failed: {exc}",
        )


class TopNRequest(BaseModel):
    user_id: int
    candidate_ids: List[int]
    top_k: int | None = 5


@router.post("/topn")
def recommend_topn(req: TopNRequest):
    try:
        from recommender.inference.recommend import score_single, enrich_item, top_popular

        results = []
        # If user unseen or models missing, fall back to popularity
        cold_start = False

        if _ml_model is not None and _ml_meta is not None:
            for mid in req.candidate_ids:
                feats = _ml_features(req.user_id, mid)
                if feats is None:
                    cold_start = True
                    continue
                try:
                    proba = _ml_model.predict_proba(feats)[0][1]
                except Exception:
                    cold_start = True
                    continue
                item_info = enrich_item(mid)
                results.append(
                    {
                        "movieId": mid,
                        "title": item_info.get("title"),
                        "tags": item_info.get("tags"),
                        "probability": float(proba),
                        "mode": "tabular",
                    }
                )
        else:
            cold_start = True

        # Try LightFM/NCF for remaining candidates or if tabular missing
        if cold_start or (not results and (_ml_model is None or _ml_meta is None)):
            for mid in req.candidate_ids:
                s = score_single(req.user_id, mid)
                item_info = enrich_item(mid)
                results.append(
                    {
                        "movieId": mid,
                        "title": item_info.get("title"),
                        "tags": item_info.get("tags"),
                        "probability": float(s.get("probability") or 0.0),
                        "mode": s.get("mode", "unknown"),
                    }
                )

        if not results:
            # popularity backoff
            results = top_popular(top_k=req.top_k or 5)

        results = sorted(results, key=lambda x: x.get("probability") or 0, reverse=True)[: req.top_k or 5]
        return {"mode": "topn", "user_id": req.user_id, "results": results}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Top-N recommendation failed: {exc}",
        )
