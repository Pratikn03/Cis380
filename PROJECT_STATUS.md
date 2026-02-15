# Project Status

## Purpose
Track current module readiness and evidence required for demo/production sign-off.

## Scope
Status table for core domains: fraud, brand/logo, voice, RAG, DSA RAG, and recommender.

## Run locally
Generate evidence and readiness reports:
```bash
python3 scripts/claim_evidence.py
python3 scripts/full_project_audit.py
python3 scripts/training_data_audit.py
```

## Test and quality commands
```bash
make quality-fast
make quality-data
make quality-test
make quality-docs-fast
```

## Ownership and canonical links
- Owner: Sentifargo Program Management
- Last verified: 2026-02-11
- Canonical docs index: `docs/README.md`
- Canonical source map: `docs/CANONICAL.md`

## Readiness table
| Module | Dataset | Model Artifact Path | Training Script | Metrics Report | API Endpoint | Demo Ready |
|---|---|---|---|---|---|---|
| Fraud (tabular) | `data/raw/fraud/creditcard.csv` | `models/fraud/supervised/fraud_model.pkl` | `src/train/train_fraud.py` | `reports/metrics_fraud.csv` | `/api/fraud` | ☐ |
| Brand/Logo (YOLO) | `data/processed/brand_yolo/brands.yaml` | `artifacts/brand/yolo_logo_det.pt` | `src/train/train_brand_logo_detector.py` | N/A | `/api/vision/brand/predict` | ☐ |
| Voice Emotion | `data/raw/voice` | `models/voice_emotion.pkl` | `scripts/voice/train_emotion_ssl.py` | N/A | `/api/voice/emotion` | ☐ |
| RAG (general) | `data/docs` | `data/embeddings` | API ingest flow | N/A | `/api/rag/ingest` | ☐ |
| DSA RAG | `data/dsa_docs` | `data/dsa_embeddings` | `app/rag_dsa/build_index.py` | N/A | `/api/dsa-rag/ask` | ☐ |
| Recommender | `data/raw/recommendation` | Runtime index | `src/train/train_recommender.py` | N/A | `/api/recommend` | ☐ |
