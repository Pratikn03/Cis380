from __future__ import annotations

from app.rag_dsa.ingest import ingest

if __name__ == "__main__":
    count = ingest()
    print(f"Indexed {count} chunks")
