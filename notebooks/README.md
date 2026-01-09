# Notebooks

This folder contains exploratory and research notebooks. It is organized into:

- `notebooks/eda/`: dataset exploration and profiling
- `notebooks/training/`: model training experiments and prototypes
- `notebooks/evaluation/`: evaluation, drift, and explainability
- `notebooks/overview/`: integration notes and end-to-end walkthroughs

The production entrypoints live under `scripts/` and `src/`.

## Key training notebooks

- `notebooks/overview/00_notebook_index.ipynb`: master index for all notebooks.
- `notebooks/training/81_face_emotion.ipynb`: 7-class face emotion training (vision).
- `notebooks/training/82_brand_logo_yolo.ipynb`: Brand/logo YOLOv8 detector training.
- `notebooks/training/83_voice_emotion.ipynb`: Voice emotion classifier training.
- `notebooks/training/84_recommender_movielens.ipynb`: MovieLens recommender baseline.
- `notebooks/training/85_recommender_multimodal_index.ipynb`: Build multimodal index.
- `notebooks/training/86_rag_ingest_query.ipynb`: RAG ingest + retrieval test.
- `notebooks/training/87_video_temporal.ipynb`: Video temporal deepfake model.
- `notebooks/training/88_action_recommender.ipynb`: Risk-action recommender (ALLOW/BLOCK, etc.).

## Key evaluation notebooks

- `notebooks/evaluation/98_metrics_audit.ipynb`: Readiness audit for metrics (95% threshold, includes YOLO runs).
