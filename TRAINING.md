# Training Operations

## Purpose
Document canonical training and data-validation commands for reproducible model workflows.

## Scope
- Data validation and split generation
- Core model training entrypoints
- Batch training scripts
- RAG index refresh and audit reporting

## Run locally
### Data validation and splits
```bash
python3 scripts/data/validate_dataset.py --task <task> --dataset <dataset> --path <path>
python3 scripts/data/make_splits.py --task <task> --dataset <dataset> --path <path>
```

### Core training entrypoints
```bash
python3 -m src.train.train_fraud
python3 -m src.train.train_cyber
python3 -m src.train.train_behavior
python3 -m src.train.train_brand_logo_detector
python3 -m src.train.train_face_emotion
python3 -m src.train.train_recommender
python3 -m src.train.train_movielens_recommender
python3 -m src.train.train_video_temporal
python3 -m src.train.train_video_temporal_lstm
```

### Batch workflows
```bash
python3 scripts/train_all.py
python3 scripts/train_all_vision.py
python3 scripts/train_all_vision_full.py
python3 scripts/train_production.py
```

### Voice emotion workflows
```bash
make train-voice      # fast MFCC/sklearn API baseline
make train-voice-ssl  # production SSL fine-tuning path
```

The MFCC baseline is useful for fast API verification, but it is not expected to
meet production voice-emotion gates on speaker-independent six-class evaluation.
Use `train-voice-ssl` with a fresh SSL output directory for production metrics.

## Test and quality commands
```bash
python3 scripts/training_data_audit.py
python3 scripts/training_gap_report.py
python3 scripts/claim_evidence.py
```

## Ownership and canonical links
- Owner: Sentifargo ML Team
- Last verified: 2026-02-11
- Canonical docs index: `docs/README.md`
- Data registry: `DATASETS.md`
- Scripts guide: `scripts/README.md`
