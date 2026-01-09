# Data Layout

Large datasets and generated artifacts are intentionally kept under `data/` and are typically ignored by git.

## Directory Structure
- `data/raw/` — raw datasets (domain-specific subfolders).
- `data/interim/` — intermediate cleaned outputs created during preprocessing.
- `data/processed/` — processed datasets and derived artifacts.
- `data/docs/` — local RAG knowledge base (markdown/txt files).
- `data/embeddings/` — local embedding/vector artifacts (RAG + recommender indexes).
- `data/monitoring/` — monitoring logs (JSONL) and baselines.

## Notes
- If some raw datasets are missing, parts of the system fall back to synthetic data to keep the demo runnable.
- Brand/logo YOLO preparation writes a YOLO-style dataset under `data/processed/brand_yolo/`.

