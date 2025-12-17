from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

from .image_embed import embed_image_bytes
from .index_store import IndexPaths, default_index_paths, save_index


class OptionalDependencyError(RuntimeError):
    pass


def _require_faiss():
    try:
        import faiss  # type: ignore

        return faiss
    except Exception as exc:  # pragma: no cover
        raise OptionalDependencyError("Multimodal recommender requires 'faiss-cpu'.") from exc


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass(frozen=True)
class BuildStats:
    images_indexed: int


def iter_images(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTS:
            yield path


def build_clip_index(
    data_dir: Path = Path("data/raw/recommendation"),
    out: IndexPaths | None = None,
    limit: int | None = None,
) -> BuildStats:
    """Build a CLIP+FAISS index from images under data_dir.

    Notes:
    - Uses CLIP image embeddings (unit norm) + FAISS IndexFlatIP (cosine similarity).
    - This is an *extension* path; it doesn't affect existing recommenders.
    """
    faiss = _require_faiss()

    out = out or default_index_paths()
    embeddings: list[np.ndarray] = []
    meta: list[dict[str, object]] = []

    for i, img_path in enumerate(iter_images(data_dir)):
        if limit is not None and i >= limit:
            break
        try:
            img_bytes = img_path.read_bytes()
            vec = embed_image_bytes(img_bytes)
        except Exception:
            continue
        embeddings.append(vec.astype(np.float32))
        meta.append({"path": str(img_path)})

    if not embeddings:
        # Create an empty index with CLIP dim=512.
        dim = 512
        index = faiss.IndexFlatIP(dim)
        save_index(index, meta, out)
        return BuildStats(images_indexed=0)

    X = np.stack(embeddings, axis=0).astype(np.float32)
    dim = int(X.shape[1])
    index = faiss.IndexFlatIP(dim)
    index.add(X)
    save_index(index, meta, out)
    return BuildStats(images_indexed=len(meta))
