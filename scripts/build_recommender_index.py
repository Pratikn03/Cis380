from __future__ import annotations

import sys
from pathlib import Path

# Allow running from repo root without installing the project as a package.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.models.recommender.features import build_embeddings, catalog_metadata  # noqa: E402
from app.models.recommender.index import RecommenderIndex, default_index_paths  # noqa: E402


def main() -> None:
    embeddings = build_embeddings()
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
