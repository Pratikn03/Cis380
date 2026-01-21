from __future__ import annotations

from app.rag.dsa_pipeline import ingest_documents


def main() -> None:
    stats = ingest_documents()
    print("[dsa] ingest complete:", stats)


if __name__ == "__main__":
    main()
