from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from app.models.recommender.multimodal.catalog import load_unified_catalog
from app.vision_local.embedder import OptionalDependencyError, embed_image_bytes, embed_text


@dataclass
class CatalogEmbeddingResult:
    df: pd.DataFrame
    vectorizer: TfidfVectorizer
    text_matrix: np.ndarray
    vectors: np.ndarray


def _normalize_metadata(text: str, brand: str | None, category: str | None) -> str:
    pieces = [text or ""]
    if brand:
        pieces.append(str(brand))
    if category:
        pieces.append(str(category))
    return " ".join(pieces).strip()


def build_catalog_dataframe() -> pd.DataFrame:
    catalog = load_unified_catalog()
    rows: list[dict[str, Any]] = []
    for key, item in catalog.items():
        rows.append(
            {
                "item_id": item.item_id,
                "title": item.title,
                "category": item.category,
                "brand": item.brand,
                "price": item.price,
                "image_path": item.image_path or "",
                "metadata": _normalize_metadata(item.title, item.brand, item.category),
                "source": key,
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.drop_duplicates(subset="item_id").reset_index(drop=True)


def _embed_semantic(image_path: str, metadata: str) -> np.ndarray:
    """Return a 512-d semantic vector for an item.

    - If an image exists, embed the image.
    - Otherwise, embed the item's metadata text into the same semantic space.

    This keeps the recommender "multimodal-ready" even when catalogs don't
    provide per-item images (common for MovieLens-style CSVs).
    """
    if image_path:
        try:
            path = Path(image_path)
            if path.exists():
                return embed_image_bytes(path.read_bytes())
        except OptionalDependencyError:
            pass
        except Exception:
            pass
    return embed_text(metadata or "")


def build_embeddings() -> CatalogEmbeddingResult:
    df = build_catalog_dataframe()
    if df.empty:
        raise RuntimeError("No recommendation catalog data available.")
    vectorizer = TfidfVectorizer(stop_words="english", max_features=2048)
    text_matrix = vectorizer.fit_transform(df["metadata"]).toarray().astype(np.float32)
    semantic_vectors = np.stack(
        [
            _embed_semantic(str(p), str(m))
            for p, m in zip(df["image_path"].tolist(), df["metadata"].tolist())
        ],
        axis=0,
    ).astype(np.float32)
    concatenated = np.concatenate([text_matrix, semantic_vectors], axis=1)
    return CatalogEmbeddingResult(
        df=df,
        vectorizer=vectorizer,
        text_matrix=text_matrix,
        vectors=concatenated,
    )


def catalog_metadata(df: pd.DataFrame) -> list[dict[str, object]]:
    return [
        {
            "item_id": row["item_id"],
            "title": row["title"],
            "category": row["category"],
            "brand": row["brand"],
            "price": row["price"],
            "source": row["source"],
            "image_path": row["image_path"],
        }
        for _, row in df.iterrows()
    ]


def embed_query_vector(
    vectorizer: TfidfVectorizer,
    text: str | None,
    image_bytes: bytes | None,
) -> np.ndarray:
    text_value = (text or "").strip()
    vec = vectorizer.transform([text_value]).toarray()[0].astype(np.float32)
    if image_bytes:
        try:
            img_vec = embed_image_bytes(image_bytes)
        except OptionalDependencyError:
            img_vec = np.zeros((512,), dtype=np.float32)
    else:
        img_vec = np.zeros((512,), dtype=np.float32)
    return np.concatenate([vec, img_vec], axis=0)
