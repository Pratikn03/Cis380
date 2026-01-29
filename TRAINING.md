# TRAINING

## Data validation + splits (offline)
- Validate dataset (directory or file):
  python scripts/data/validate_dataset.py --task <task> --dataset <dataset> --path <path>

- Create splits (directory or CSV file):
  python scripts/data/make_splits.py --task <task> --dataset <dataset> --path <path>

## Model training entrypoints (existing)
- Fraud:
  python -m src.train.train_fraud
- Cyber:
  python -m src.train.train_cyber
- Behavior:
  python -m src.train.train_behavior
  # Optional insider-pattern augmentation (default enabled in configs/behavior_config.yaml):
  #   BEHAVIOR_AUGMENT_INSIDER=true
  #   BEHAVIOR_INSIDER_RATIO=0.05
  #   BEHAVIOR_INSIDER_MAX_ROWS=1500
  # False-positive comparison (baseline vs augmented):
  python scripts/compare_behavior_fp.py
- Brand/Logo (YOLO):
  python -m src.train.train_brand_logo_detector
- Brand (multi-class car/fashion):
  python scripts/prepare_brand_data.py --kind car
  BRAND_KIND=car python -m src.train.train_brand_logo_detector
  python scripts/prepare_brand_data.py --kind fashion
  BRAND_KIND=fashion python -m src.train.train_brand_logo_detector
  # Or run the helper:
  python scripts/train_brand_multiclass.py --kind car
- Face emotion:
  python -m src.train.train_face_emotion
- Recommender:
  python -m src.train.train_recommender
- MovieLens recommender:
  python -m src.train.train_movielens_recommender
- Video temporal:
  python -m src.train.train_video_temporal
  python -m src.train.train_video_temporal_lstm
  # LSTM drift monitor (writes reports/vision_temporal_lstm_drift.json)
  python scripts/monitor_video_temporal_drift.py
- Speech-to-Text (STT) data + fine-tuning:
  # Bootstrap transcripts (offline Whisper)
  python scripts/stt/bootstrap_transcripts.py --audio-root data/raw/voice/AudioWAV --out data/raw/stt/transcripts.jsonl --language en
  python scripts/stt/build_manifest.py --transcripts data/raw/stt/transcripts.jsonl --out data/raw/stt/manifest.csv --normalize --require-text
  python scripts/stt/split_manifest.py --manifest data/raw/stt/manifest.csv --group-by speaker_id
  # Evaluate WER/CER
  python scripts/stt/evaluate_stt.py --manifest data/raw/stt/manifest.with_splits.csv --split test --normalize
  # Fine-tune Whisper (optional)
  python scripts/stt/train_whisper.py --train-manifest data/raw/stt/manifest.train.csv --val-manifest data/raw/stt/manifest.val.csv --model openai/whisper-small --normalize --augment

## Batch training shortcuts
- python scripts/train_all.py
- python scripts/train_all.py --with-stt --stt-bootstrap-limit 200
- python scripts/train_all_vision.py
- python scripts/train_all_vision_full.py
- python scripts/train_production.py

## RAG indexing (offline)
- General RAG (API-driven):
  POST /api/rag/ingest
- DSA RAG:
  python -m app.rag_dsa.build_index

## Training audits / reports
- python scripts/training_data_audit.py
- python scripts/training_gap_report.py
- python scripts/claim_evidence.py
