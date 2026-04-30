# Voice Emotion Scripts

## Purpose
Define the production-oriented voice emotion training and evaluation pipeline.

## Scope
- Dataset audit and manifest build
- Speaker-independent split creation
- SSL model training
- Evaluation metrics workflow

## Run locally
Fast API baseline:
```bash
make train-voice
```

Production SSL path:
```bash
python3 scripts/voice/audit_voice_dataset.py --data-root data/raw/voice --pattern '^(?P<speaker>\\d{4})_.*\\.wav$'
python3 scripts/prepare_voice_from_audiowav.py --mode link
python3 scripts/voice/build_emotion_manifest.py --data-root data/raw/voice --out data/raw/voice/manifest.csv
python3 scripts/voice/split_manifest.py --manifest data/raw/voice/manifest.csv --out-dir data/raw/voice --train-ratio 0.8 --val-ratio 0.1 --test-ratio 0.1
make train-voice-ssl
```

Use a fresh SSL output directory for class-set changes. The trainer rejects stale
SSL directories whose saved label map does not match the current manifest.

## Test and quality commands
```bash
python3 scripts/voice/eval_emotion_ssl.py --model-dir models/voice_emotion_ssl_6class --test-manifest data/raw/voice/manifest.test.csv
python3 scripts/quality/docs_quality_check.py --mode fast --threshold 85
```

## Ownership and canonical links
- Owner: Sentifargo Speech Team
- Last verified: 2026-02-11
- Canonical scripts guide: `../README.md`
- Canonical docs index: `../../docs/README.md`
