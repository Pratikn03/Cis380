# STT Scripts

## Purpose
Define the offline-first speech-to-text dataset pipeline and optional fine-tuning flow.

## Scope
- Transcript bootstrap
- Manifest build/split/validation
- WER/CER evaluation
- Optional Whisper fine-tuning

## Run locally
```bash
python3 scripts/stt/bootstrap_transcripts.py --audio-root data/raw/voice/AudioWAV --out data/raw/stt/transcripts.jsonl --language en
python3 scripts/stt/build_manifest.py --transcripts data/raw/stt/transcripts.jsonl --out data/raw/stt/manifest.csv --normalize
python3 scripts/stt/split_manifest.py --manifest data/raw/stt/manifest.csv --seed 42 --group-by speaker_id
python3 scripts/stt/validate_manifest.py --manifest data/raw/stt/manifest.csv
python3 scripts/stt/evaluate_stt.py --manifest data/raw/stt/manifest.with_splits.csv --split test --limit 100
```

## Test and quality commands
```bash
python3 scripts/stt/evaluate_stt.py --manifest data/raw/stt/manifest.with_splits.csv --split test
python3 scripts/quality/docs_quality_check.py --mode fast --threshold 85
```

## Ownership and canonical links
- Owner: Sentifargo Speech Team
- Last verified: 2026-02-11
- Canonical scripts guide: `../README.md`
- Canonical docs index: `../../docs/README.md`
