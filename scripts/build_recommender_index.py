from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Allow running from repo root without installing the project as a package.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.models.recommender.features import build_embeddings, catalog_metadata  # noqa: E402
from app.models.recommender.index import RecommenderIndex, default_index_paths  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build recommender vector + FAISS index artifacts."
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=0,
        help="Cap number of catalog items embedded (0 uses all). Useful for quick smoke tests.",
    )
    parser.add_argument(
        "--embed-backend",
        choices=["auto", "fallback"],
        default="auto",
        help="Embedding backend for semantic vectors. 'fallback' is fast and fully offline.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Sampling seed used when --max-items is set.",
    )
    args = parser.parse_args()

    os.environ.setdefault("Sentifargo_EMBEDDINGS_BACKEND", str(args.embed_backend))
    os.environ.setdefault(
        "Sentifargo_EMBEDDINGS_BACKEND", os.environ["Sentifargo_EMBEDDINGS_BACKEND"]
    )
    max_items = int(args.max_items) if int(args.max_items) > 0 else None
    embeddings = build_embeddings(max_items=max_items, seed=int(args.seed))
    meta = catalog_metadata(embeddings.df)
    paths = default_index_paths()
    index = RecommenderIndex(embeddings.vectors, meta, paths=paths)
    index.build()
    print(f"Saved recommender vectors to {paths.vectors_path}")
    if _has_faiss():
        print(f"Saved FAISS index to {paths.index_path}")
    print(f"Saved metadata to {paths.meta_path}")


def _has_faiss() -> bool:
    try:
        import faiss  # noqa: F401

        return True
    except ImportError:
        return False


if __name__ == "__main__":
    main()
