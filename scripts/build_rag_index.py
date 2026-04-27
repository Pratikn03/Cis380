from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the production RAG index.")
    parser.add_argument("--model", default="BAAI/bge-small-en-v1.5")
    parser.add_argument("--docs-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--rebuild", action="store_true", default=True)
    parser.add_argument(
        "--backend",
        choices=["auto", "sentence_transformer", "hashing"],
        default="auto",
        help="Embedding backend. Hashing is deterministic and offline-safe.",
    )
    args = parser.parse_args()

    os.environ["RAG_EMBED_MODEL"] = args.model
    os.environ["RAG_EMBED_BACKEND"] = args.backend
    if args.docs_dir is not None:
        os.environ["RAG_DOCS_DIR"] = str(args.docs_dir)
    if args.output_dir is not None:
        os.environ["RAG_OUTPUT_DIR"] = str(args.output_dir)

    from app.rag.config import settings
    from app.rag.dsa_pipeline import ingest_documents

    stats = ingest_documents(rebuild=bool(args.rebuild))
    meta_path = settings.index_meta_path
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    else:
        meta = {}
    meta.update({"requested_model": args.model, "backend": args.backend, "stats": stats})
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("[rag-index] complete:", json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
