# PROJECT STATUS (Truth Audit)

| Module | Dataset | Model Artifact Path | Training Script | Metrics Report | API Endpoint | Demo Ready |
|---|---|---|---|---|---|---|
| Fraud (tabular) | data/raw/fraud/creditcard.csv (configs/data_fraud.yaml) | models/fraud/supervised/fraud_model.pkl | src/train/train_fraud.py | reports/metrics_fraud.csv | /api/fraud | ☐ |
| Brand/Logo (YOLO) | data/processed/brand_yolo/brands.yaml | artifacts/brand/yolo_logo_det.pt (default) | src/train/train_brand_logo_detector.py | — | /api/vision/brand/predict | ☐ |
| Voice Emotion | data/raw/crema_d + data/raw/voice | models/voice_emotion.pkl | N/A (fallback model in app/models/voice/emotion_predict.py) | — | /api/voice/emotion | ☐ |
| RAG (general) | data/docs | data/embeddings | /api/rag/ingest (builds index) | — | /api/rag/ingest | ☐ |
| DSA RAG | data/dsa_docs | data/dsa_embeddings | app/rag_dsa/build_index.py | — | /api/dsa-rag/ask | ☐ |
| Recommender (catalog) | data/catalogs/*.jsonl | N/A (catalog embeddings built at runtime) | src/train/train_recommender.py | — | /api/recommend | ☐ |

Notes:
- Demo Ready = endpoint works + sample exists + standard response envelope.
