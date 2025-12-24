from pathlib import Path
from typing import List, Optional

import joblib
import numpy as np
from fastapi import APIRouter, HTTPException, status, Depends, File, Form, UploadFile
from pydantic import BaseModel, Field

from api.deps import require_auth

# Optional multimodal extension (must not break if deps/index missing)
try:  # pragma: no cover
    from app.models.recommender.multimodal import multimodal_predict as _mm
except Exception:  # pragma: no cover
    _mm = None

router = APIRouter(
    prefix="/api/recommend", tags=["recommend"], dependencies=[Depends(require_auth)]
)


class RecommendRequest(BaseModel):
    # Option A: "items" recommender (app/models/recommender) used by tests + demo.
    user_id: str | int | None = None
    top_k: int | None = Field(default=5, ge=1, le=20)

    # Option B: MovieLens-style point scoring (legacy)
    movie_id: Optional[int] = None

    # Option C: generic numeric vector (legacy)
    features: Optional[List[float]] = None
    candidate_ids: Optional[List[int]] = None  # for top-N from a provided set


PROJECT_ROOT = Path(__file__).resolve().parents[2]

# generic/tabular recommender (XGBoost)
_rec_path = PROJECT_ROOT / "recommender" / "models" / "recommender.pkl"
_rec_model = None
_rec_model_error: str | None = None

# MovieLens model/meta (uses same xgboost by default)
_ml_model_path = PROJECT_ROOT / "recommender" / "models" / "recommender.pkl"
_ml_meta_path = PROJECT_ROOT / "recommender" / "models" / "recommender_meta.joblib"
_ml_model = None
_ml_model_error: str | None = None
_ml_meta = None
_ml_meta_error: str | None = None


def _get_rec_model():
    global _rec_model, _rec_model_error
    if _rec_model is not None:
        return _rec_model
    if not _rec_path.exists():
        return None
    if _rec_model_error is not None:
        return None
    try:
        _rec_model = joblib.load(_rec_path)
    except Exception as exc:  # pragma: no cover - depends on local env
        _rec_model_error = str(exc)
        return None
    return _rec_model


def _get_ml_model():
    global _ml_model, _ml_model_error
    if _ml_model is not None:
        return _ml_model
    if not _ml_model_path.exists():
        return None
    if _ml_model_error is not None:
        return None
    try:
        _ml_model = joblib.load(_ml_model_path)
    except Exception as exc:  # pragma: no cover - depends on local env
        _ml_model_error = str(exc)
        return None
    return _ml_model


def _get_ml_meta():
    global _ml_meta, _ml_meta_error
    if _ml_meta is not None:
        return _ml_meta
    if not _ml_meta_path.exists():
        return None
    if _ml_meta_error is not None:
        return None
    try:
        _ml_meta = joblib.load(_ml_meta_path)
    except Exception as exc:  # pragma: no cover - depends on local env
        _ml_meta_error = str(exc)
        return None
    return _ml_meta


def _ml_features(user_id: int, movie_id: int):
    meta = _get_ml_meta()
    if meta is None:
        return None
    user_stats = meta.get("user_stats")
    item_stats = meta.get("item_stats")
    global_mean = meta.get("global_mean", 3.5)
    user_codes = meta.get("user_codes", {})
    item_codes = meta.get("item_codes", {})
    feat_names = meta.get("feature_names", [])

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
    # Path A: MovieLens-style if user_id and movie_id provided and model exists.
    ml_model = _get_ml_model()
    if isinstance(req.user_id, int) and req.movie_id is not None and ml_model is not None:
        try:
            ml_feats = _ml_features(req.user_id, req.movie_id)
            if ml_feats is None:
                raise ValueError("MovieLens metadata not available.")
            feats, names = ml_feats
            proba = ml_model.predict_proba(feats)[0]
            classes = list(getattr(ml_model, "classes_", []))
            top_idx = int(np.argmax(proba))
            raw_label = classes[top_idx] if classes else "like"
            label = raw_label.item() if isinstance(raw_label, np.generic) else raw_label
            return {
                "mode": "movielens",
                "user_id": req.user_id,
                "movie_id": req.movie_id,
                "label": label,
                "probability": float(proba[top_idx]),
                "feature_names": names,
            }
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"MovieLens recommendation failed: {exc}",
            )

    # Path B: app-style "items" recommender when top_k is provided and no explicit vector request.
    if req.features is None and req.movie_id is None:
        try:
            from app.models.recommender.predict import recommend as recommend_items

            uid = "anon" if req.user_id is None else str(req.user_id)
            items = recommend_items(user_id=uid, top_k=int(req.top_k or 5))
            return {"mode": "items", "user_id": uid, "items": items}
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Item recommendation failed: {exc}",
            )

    # Path C: generic vector fallback.
    rec_model = _get_rec_model()
    if rec_model is None:
        detail = "Recommender model not found."
        if _rec_path.exists() and _rec_model_error:
            detail = f"Recommender model failed to load: {_rec_model_error}"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )
    feats = req.features or []
    try:
        n = getattr(rec_model, "n_features_in_", 0)
        arr = np.zeros((1, n), dtype=float)
        for i, v in enumerate(feats[:n]):
            arr[0, i] = v
        if hasattr(rec_model, "predict_proba"):
            proba = rec_model.predict_proba(arr)[0]
            classes = list(getattr(rec_model, "classes_", []))
            top_idx = int(np.argmax(proba))
            raw_label = classes[top_idx] if classes else "item"
            label = raw_label.item() if isinstance(raw_label, np.generic) else raw_label
            result = {"label": label, "probability": float(proba[top_idx])}
        else:
            label = rec_model.predict(arr)[0]
            result = {"label": str(label), "probability": None}
        return {"mode": "generic", "input_filled": len(feats), "result": result}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation failed: {exc}",
        )


class ExplainRequest(BaseModel):
    user_id: str | int | None = None
    item_id: str


@router.post("/explain")
def explain(req: ExplainRequest):
    try:
        from app.models.recommender.explain import explain_recommendation

        uid = "anon" if req.user_id is None else str(req.user_id)
        text = explain_recommendation(uid, req.item_id)
        return {"explanation": text}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Explanation failed: {exc}",
        )


@router.post("/multimodal")
async def recommend_multimodal(
    text: Optional[str] = Form(default=None),
    top_k: int = Form(default=5, ge=1, le=20),
    image: UploadFile | None = File(default=None),
):
    """CLIP + FAISS multimodal recommender (additive).

    Provide either a text query or an uploaded image. If the index isn't built yet,
    this endpoint returns 503 with instructions.
    """
    try:
        image_bytes = await image.read() if image is not None else None
        if _mm is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Multimodal recommender dependencies are not available.",
            )
        return _mm.multimodal_recommend(image_bytes=image_bytes, text=text, top_k=top_k)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        if _mm is not None and isinstance(exc, _mm.IndexNotBuiltError):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multimodal recommendation failed: {exc}",
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

        ml_model = _get_ml_model()
        ml_meta = _get_ml_meta()
        if ml_model is not None and ml_meta is not None:
            for mid in req.candidate_ids:
                feats = _ml_features(req.user_id, mid)
                if feats is None:
                    cold_start = True
                    continue
                try:
                    proba = ml_model.predict_proba(feats)[0][1]
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
        if cold_start:
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

        results = sorted(results, key=lambda x: x.get("probability") or 0, reverse=True)[
            : req.top_k or 5
        ]
        return {"mode": "topn", "user_id": req.user_id, "results": results}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Top-N recommendation failed: {exc}",
        )
