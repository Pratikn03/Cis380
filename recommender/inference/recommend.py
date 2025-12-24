"""Inference helper for hybrid recommender (tabular classifier)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import joblib
import numpy as np
import torch
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "recommender" / "models" / "recommender.pkl"  # tabular GBM
META_PATH = PROJECT_ROOT / "recommender" / "models" / "recommender_meta.joblib"
LIGHTFM_PATH = PROJECT_ROOT / "recommender" / "models" / "recommender_lightfm.npz"
LIGHTFM_META = PROJECT_ROOT / "recommender" / "models" / "recommender_lightfm_meta.joblib"
NCF_PATH = PROJECT_ROOT / "recommender" / "models" / "recommender_ncf.pt"
NCF_META = PROJECT_ROOT / "recommender" / "models" / "recommender_ncf_meta.joblib"
ITEMS_PATH = PROJECT_ROOT / "data" / "raw" / "recommendation" / "items.csv"


def load_model(path: Path = MODEL_PATH) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Model not found at {path}")
    return joblib.load(path)


def load_meta(path: Path = META_PATH) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Meta not found at {path}")
    return joblib.load(path)


def load_items() -> pd.DataFrame:
    if ITEMS_PATH.exists():
        try:
            df = pd.read_csv(ITEMS_PATH)
            # expect movieId,title,tags,popularity
            cols = {c.lower(): c for c in df.columns}
            id_col = cols.get("movieid", "movieId")
            title_col = cols.get("title", "title")
            tags_col = cols.get("tags", "tags")
            pop_col = cols.get("popularity", "popularity")
            df = df.rename(
                columns={
                    id_col: "movieId",
                    title_col: "title",
                    tags_col: "tags",
                    pop_col: "popularity",
                }
            )
            if "popularity" not in df:
                df["popularity"] = 0.0
            return df[["movieId", "title", "tags", "popularity"]]
        except Exception:
            pass
    return pd.DataFrame(columns=["movieId", "title", "tags", "popularity"])


ITEMS_META = load_items()


def enrich_item(movie_id: int) -> Dict[str, Any]:
    if ITEMS_META.empty:
        return {"movieId": movie_id, "title": f"movie {movie_id}", "tags": "", "popularity": 0}
    row = ITEMS_META[ITEMS_META["movieId"] == movie_id]
    if row.empty:
        return {"movieId": movie_id, "title": f"movie {movie_id}", "tags": "", "popularity": 0}
    r = row.iloc[0]
    return {
        "movieId": int(r["movieId"]),
        "title": str(r["title"]),
        "tags": str(r["tags"]),
        "popularity": float(r["popularity"]),
    }


def top_popular(top_k: int = 5):
    if ITEMS_META.empty:
        return []
    df = ITEMS_META.copy()
    df = df.sort_values(by="popularity", ascending=False)
    return [
        {
            "movieId": int(r["movieId"]),
            "title": str(r["title"]),
            "tags": str(r["tags"]),
            "probability": None,
            "mode": "popularity",
        }
        for _, r in df.head(top_k).iterrows()
    ]


def build_feature_row(user_id: int, item_id: int, meta: Dict[str, Any]) -> np.ndarray:
    user_stats = meta.get("user_stats")
    item_stats = meta.get("item_stats")
    global_mean = meta.get("global_mean", 3.5)
    user_codes = meta.get("user_codes", {})
    item_codes = meta.get("item_codes", {})
    feat_names = meta.get("feature_names", [])

    u_mean = user_stats.loc[user_id]["user_mean"] if user_id in user_stats.index else global_mean
    u_count = user_stats.loc[user_id]["user_count"] if user_id in user_stats.index else 0.0
    i_mean = item_stats.loc[item_id]["item_mean"] if item_id in item_stats.index else global_mean
    i_count = item_stats.loc[item_id]["item_count"] if item_id in item_stats.index else 0.0
    u_code = user_codes.get(user_id, 0)
    i_code = item_codes.get(item_id, 0)

    values = {
        "user_mean": u_mean,
        "item_mean": i_mean,
        "user_count": u_count,
        "item_count": i_count,
        "global_mean": global_mean,
        "user_code": u_code,
        "item_code": i_code,
    }
    return np.array([[values.get(k, 0.0) for k in feat_names]])


def score_single(user_id: int, item_id: int) -> Dict[str, Any]:
    # Try LightFM first if available
    if LIGHTFM_PATH.exists() and LIGHTFM_META.exists():
        try:
            from lightfm import LightFM  # type: ignore

            meta = joblib.load(LIGHTFM_META)
            users = meta.get("users", [])
            items = meta.get("items", [])
            if user_id in users and item_id in items:
                model = LightFM().load(str(LIGHTFM_PATH))
                u_idx = users.index(user_id)
                i_idx = items.index(item_id)
                score = float(model.predict(u_idx, np.array([i_idx]))[0])
                return {
                    "label": "like",
                    "probability": score,
                    "mode": "lightfm",
                    "explanation": f"Approximate latent score (LightFM WARP): {score:.3f}",
                }
        except Exception:
            pass

    # Try NCF if available
    if NCF_PATH.exists() and NCF_META.exists():
        from recommender.models.train_ncf import NCF  # reuse class

        meta_ncf = joblib.load(NCF_META)
        user_codes = meta_ncf.get("user_codes", {})
        item_codes = meta_ncf.get("item_codes", {})
        num_users = meta_ncf.get("num_users", 0)
        num_items = meta_ncf.get("num_items", 0)
        if user_id in user_codes and item_id in item_codes:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            model = NCF(num_users, num_items, emb_size=32).to(device)
            model.load_state_dict(torch.load(NCF_PATH, map_location=device))
            model.eval()
            u = torch.tensor([user_codes[user_id]], device=device)
            i = torch.tensor([item_codes[item_id]], device=device)
            with torch.no_grad():
                prob = float(model(u, i).cpu().numpy()[0])
            return {
                "label": "like" if prob >= 0.5 else "skip",
                "probability": prob,
                "mode": "ncf",
                "explanation": f"Approximate NCF probability: {prob:.3f}",
            }

    # Fallback to tabular
    model = load_model()
    meta = load_meta()
    feats = build_feature_row(user_id, item_id, meta)
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(feats)[0]
        classes = getattr(model, "classes_", [])
        top_idx = int(np.argmax(proba))
        label = classes[top_idx] if len(classes) > top_idx else "like"
        return {
            "label": label,
            "probability": float(proba[top_idx]),
            "classes": list(classes),
            "mode": "tabular",
        }
    pred = model.predict(feats)[0]
    return {"label": str(pred), "probability": None, "classes": [], "mode": "tabular"}
