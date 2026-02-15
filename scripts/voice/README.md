# Voice Emotion Scripts

## Purpose
Define the production-oriented voice emotion training and evaluation pipeline.

## Scope
- Dataset audit and manifest build
- Speaker-independent split creation
- SSL model training
- Evaluation metrics workflow

## Run locally
```bash
python3 scripts/voice/audit_voice_dataset.py --data-root data/raw/voice --pattern '^(?P<speaker>\\d{4})_.*\\.wav$'
python3 scripts/voice/build_emotion_manifest.py --data-root data/raw/voice --out data/raw/voice/manifest.csv
python3 scripts/voice/split_manifest.py --manifest data/raw/voice/manifest.csv --out-dir data/raw/voice --train-ratio 0.8 --val-ratio 0.1 --test-ratio 0.1
python3 scripts/voice/train_emotion_ssl.py --train-manifest data/raw/voice/manifest.train.csv --val-manifest data/raw/voice/manifest.val.csv --model microsoft/wavlm-base-plus --output-dir models/voice_emotion_ssl
python3 scripts/voice/eval_emotion_ssl.py --model-dir models/voice_emotion_ssl --test-manifest data/raw/voice/manifest.test.csv
```

## Test and quality commands
```bash
python3 scripts/voice/eval_emotion_ssl.py --model-dir models/voice_emotion_ssl --test-manifest data/raw/voice/manifest.test.csv
python3 scripts/quality/docs_quality_check.py --mode fast --threshold 85
```

## Ownership and canonical links
- Owner: Sentifargo Speech Team
- Last verified: 2026-02-11
- Canonical scripts guide: `../README.md`
- Canonical docs index: `../../docs/README.md`
