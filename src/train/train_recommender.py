"""Train a two-tower retrieval recommender and report ranking metrics."""

from __future__ import annotations

import json
import os
import pickle
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import HashingVectorizer

DATA_ROOT = Path("data/raw/recommendation")
OUT_MODEL = Path("models/recommender/recommender_model.pkl")
OUT_META = Path("models/recommender/recommender_meta.joblib")
OUT_METRICS = Path("experiments/recommender/metrics/metrics.json")


def _read_csv(path: Path, *, nrows: int | None = None) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, nrows=nrows)


def _load_movielens(nrows: int | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    ratings_path = DATA_ROOT / "archive (5)" / "rating.csv"
    movies_path = DATA_ROOT / "archive (5)" / "movie.csv"
    ratings = _read_csv(ratings_path, nrows=nrows)
    movies = _read_csv(movies_path)
    if ratings.empty or movies.empty:
        return pd.DataFrame(), pd.DataFrame()
    ratings = ratings.rename(columns={"userId": "user_id", "movieId": "item_id"})
    movies = movies.rename(columns={"movieId": "item_id"})
    movies["text"] = (
        movies.get("title", "").astype(str) + " " + movies.get("genres", "").astype(str)
    ).str.strip()
    keep = ["user_id", "item_id", "rating"]
    if "timestamp" in ratings.columns:
        keep.append("timestamp")
    return ratings[keep], movies[["item_id", "text"]]


def _load_books(nrows: int | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    ratings_path = DATA_ROOT / "archive (14)" / "ratings.csv"
    books_path = DATA_ROOT / "archive (14)" / "books.csv"
    ratings = _read_csv(ratings_path, nrows=nrows)
    books = _read_csv(books_path)
    if ratings.empty or books.empty:
        return pd.DataFrame(), pd.DataFrame()
    ratings = ratings.rename(columns={"book_id": "item_id"})
    title_col = next((c for c in ("title", "original_title", "authors") if c in books), None)
    if title_col is None:
        books["text"] = books["book_id"].astype(str)
    else:
        books["text"] = books[title_col].astype(str)
    books = books.rename(columns={"book_id": "item_id"})
    return ratings[["user_id", "item_id", "rating"]], books[["item_id", "text"]]


def _synthetic_interactions() -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(42)
    users = np.repeat(np.arange(50), 12)
    items = rng.integers(0, 100, size=len(users))
    ratings = rng.choice([3.0, 4.0, 5.0], size=len(users), p=[0.25, 0.45, 0.30])
    interactions = pd.DataFrame({"user_id": users, "item_id": items, "rating": ratings})
    catalog = pd.DataFrame(
        {
            "item_id": np.arange(100),
            "text": [f"synthetic item {i} category {i % 7}" for i in range(100)],
        }
    )
    return interactions, catalog


def load_interactions() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    sample_env = os.getenv("Sentifargo_RECOMMENDER_SAMPLE_SIZE")
    nrows = int(sample_env) if sample_env and int(sample_env) > 0 else None
    interactions, catalog = _load_movielens(nrows)
    source = "movielens"
    if interactions.empty:
        interactions, catalog = _load_books(nrows)
        source = "books"
    if interactions.empty:
        interactions, catalog = _synthetic_interactions()
        source = "synthetic"
    interactions = interactions.dropna(subset=["user_id", "item_id", "rating"]).copy()
    interactions["user_id"] = interactions["user_id"].astype(str)
    interactions["item_id"] = interactions["item_id"].astype(str)
    interactions["rating"] = pd.to_numeric(interactions["rating"], errors="coerce").fillna(0.0)
    if "timestamp" in interactions.columns:
        interactions["timestamp"] = pd.to_datetime(interactions["timestamp"], errors="coerce")
    else:
        interactions["timestamp"] = pd.NaT
    interactions["_input_order"] = np.arange(len(interactions), dtype=np.int64)
    catalog = catalog.dropna(subset=["item_id"]).drop_duplicates("item_id").copy()
    catalog["item_id"] = catalog["item_id"].astype(str)
    catalog["text"] = catalog.get("text", catalog["item_id"]).astype(str)
    return interactions, catalog, {"source": source, "nrows": nrows}


def embed_items(texts: list[str]) -> tuple[np.ndarray, dict[str, Any]]:
    model_name = os.getenv("RECOMMENDER_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    backend = os.getenv("RECOMMENDER_EMBED_BACKEND", "auto").strip().lower()
    if backend not in {"auto", "sentence_transformer", "hashing"}:
        backend = "auto"
    if backend != "hashing":
        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(model_name)
            vectors = np.asarray(model.encode(texts, convert_to_numpy=True), dtype=np.float32)
            return vectors, {
                "backend": "sentence_transformer",
                "model": model_name,
                "dim": int(vectors.shape[1]),
            }
        except Exception as exc:
            if backend == "sentence_transformer":
                raise
            print(f"[recommender] sentence-transformers unavailable; using hashing ({exc}).")

    vectorizer = HashingVectorizer(
        n_features=384,
        stop_words="english",
        alternate_sign=False,
        norm="l2",
    )
    vectors = vectorizer.transform(texts).toarray().astype(np.float32)
    return vectors, {"backend": "hashing", "model": "HashingVectorizer", "dim": int(vectors.shape[1])}


def _normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms = np.clip(norms, 1e-8, None)
    return matrix / norms


def build_train_eval(interactions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    positives = interactions[interactions["rating"] >= 4.0].copy()
    if positives.empty:
        positives = interactions.copy()
    positives = positives.drop_duplicates(["user_id", "item_id"])
    sort_cols = ["user_id", "timestamp", "_input_order"] if "timestamp" in positives else ["user_id", "_input_order"]
    positives = positives.sort_values(sort_cols, kind="mergesort")
    positives["_rank"] = positives.groupby("user_id").cumcount()
    counts = positives.groupby("user_id")["item_id"].transform("count")
    eligible = positives[counts >= 2].copy()
    if eligible.empty:
        return positives, positives.head(0)
    holdout_idx = eligible.groupby("user_id").tail(1).index
    test = positives.loc[holdout_idx].copy()
    train = positives.drop(index=holdout_idx).copy()
    return train, test


def build_transition_index(
    train: pd.DataFrame,
    *,
    max_next_items: int = 100,
) -> dict[str, list[tuple[str, int]]]:
    """Learn item-to-next-item transitions from positive user sequences."""
    transitions: dict[str, Counter[str]] = defaultdict(Counter)
    ordered = train.sort_values(["user_id", "timestamp", "_input_order"], kind="mergesort")
    for _, group in ordered.groupby("user_id", sort=False):
        items = group["item_id"].astype(str).tolist()
        for current, nxt in zip(items, items[1:]):
            if current != nxt:
                transitions[current][nxt] += 1
    return {
        item: counter.most_common(max_next_items)
        for item, counter in transitions.items()
        if counter
    }


def evaluate_ranking(
    *,
    train: pd.DataFrame,
    test: pd.DataFrame,
    item_ids: list[str],
    item_vectors: np.ndarray,
    transition_index: dict[str, list[tuple[str, int]]] | None = None,
    popularity: list[str] | None = None,
    k: int = 10,
) -> dict[str, float | int]:
    item_index = {item_id: idx for idx, item_id in enumerate(item_ids)}
    user_groups = train.groupby("user_id")["item_id"].apply(list).to_dict()
    eval_users = test["user_id"].drop_duplicates().tolist()
    max_users = int(os.getenv("Sentifargo_RECOMMENDER_EVAL_USERS", "0"))
    if max_users > 0 and len(eval_users) > max_users:
        eval_users = eval_users[:max_users]

    recalls: list[float] = []
    ndcgs: list[float] = []
    normalized_items = _normalize(item_vectors)
    transition_index = transition_index or {}
    popularity = popularity or []
    for user_id in eval_users:
        history = [item for item in user_groups.get(user_id, []) if item in item_index]
        truth = [
            item
            for item in test.loc[test["user_id"] == user_id, "item_id"].astype(str).tolist()
            if item in item_index
        ]
        if not history or not truth:
            continue
        seen = set(history)
        candidate_scores: dict[str, float] = {}
        recent = list(reversed(history[-20:]))
        for offset, item in enumerate(recent):
            recency_weight = 1.0 / float(offset + 1)
            for candidate, count in transition_index.get(item, []):
                if candidate not in seen and candidate in item_index:
                    candidate_scores[candidate] = candidate_scores.get(candidate, 0.0) + (
                        recency_weight * np.log1p(float(count))
                    )

        ranked = [
            item
            for item, _ in sorted(candidate_scores.items(), key=lambda pair: pair[1], reverse=True)
        ][:k]

        if len(ranked) < k:
            for item in popularity:
                if item not in seen and item not in ranked:
                    ranked.append(item)
                    if len(ranked) >= k:
                        break

        if len(ranked) < k:
            profile = normalized_items[[item_index[item] for item in history]].mean(axis=0)
            norm = np.linalg.norm(profile)
            if norm > 0:
                profile = profile / norm
            scores = normalized_items @ profile
            for item in seen:
                scores[item_index[item]] = -np.inf
            for item in ranked:
                scores[item_index[item]] = -np.inf
            top_idx = np.argsort(scores)[::-1][: max(0, k - len(ranked))]
            ranked.extend([item_ids[idx] for idx in top_idx])

        truth_set = set(truth)
        hits = [idx for idx, item in enumerate(ranked, start=1) if item in truth_set]
        recalls.append(float(len(hits) / max(1, len(truth_set))))
        ndcgs.append(float(1.0 / np.log2(hits[0] + 1)) if hits else 0.0)

    return {
        "recall_at_10": float(np.mean(recalls)) if recalls else 0.0,
        "ndcg_at_10": float(np.mean(ndcgs)) if ndcgs else 0.0,
        "eval_users": int(len(recalls)),
        "train_interactions": int(len(train)),
        "test_interactions": int(len(test)),
        "item_count": int(len(item_ids)),
    }


def main() -> None:
    interactions, catalog, source_meta = load_interactions()
    train, test = build_train_eval(interactions)
    item_ids = catalog["item_id"].astype(str).tolist()
    item_vectors, embed_meta = embed_items(catalog["text"].astype(str).tolist())
    transition_index = build_transition_index(train)
    popularity = train["item_id"].astype(str).value_counts().index.tolist()

    metrics = evaluate_ranking(
        train=train,
        test=test,
        item_ids=item_ids,
        item_vectors=item_vectors,
        transition_index=transition_index,
        popularity=popularity,
        k=10,
    )
    metrics.update(source_meta)
    metrics["embedding"] = embed_meta

    user_profiles: dict[str, np.ndarray] = {}
    normalized_items = _normalize(item_vectors)
    item_index = {item_id: idx for idx, item_id in enumerate(item_ids)}
    for user_id, history in train.groupby("user_id")["item_id"].apply(list).items():
        idxs = [item_index[str(item)] for item in history if str(item) in item_index]
        if idxs:
            user_profiles[str(user_id)] = normalized_items[idxs].mean(axis=0).astype(np.float32)

    OUT_MODEL.parent.mkdir(parents=True, exist_ok=True)
    with OUT_MODEL.open("wb") as handle:
        pickle.dump(
            {
                "item_ids": item_ids,
                "item_vectors": item_vectors.astype(np.float32),
                "item_metadata": catalog.to_dict(orient="records"),
                "user_profiles": user_profiles,
                "transition_index": transition_index,
                "popularity": popularity[:1000],
                "embedding": embed_meta,
            },
            handle,
        )
    with OUT_META.open("wb") as handle:
        pickle.dump(
            {
                "source": source_meta,
                "embedding": embed_meta,
                "metrics": metrics,
            },
            handle,
        )

    OUT_METRICS.parent.mkdir(parents=True, exist_ok=True)
    OUT_METRICS.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Saved recommender model to {OUT_MODEL}")
    print(f"Saved recommender meta to {OUT_META}")
    print(f"Metrics written to {OUT_METRICS}")


if __name__ == "__main__":
    main()
