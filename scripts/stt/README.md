# STT Dataset Pipeline (Offline)

This folder builds a **speech-to-text (STT)** dataset from local audio.
It is **offline-first** and uses `faster-whisper` for bootstrapping transcripts.

## 1) Bootstrap transcripts (from audio)

```bash
python scripts/stt/bootstrap_transcripts.py \
  --audio-root data/raw/voice/AudioWAV \
  --out data/raw/stt/transcripts.jsonl \
  --language en \
  --limit 200
```

Fast full‑dataset bootstrap (CREMA‑D sentence codes):

```bash
python scripts/stt/bootstrap_transcripts.py \
  --audio-root data/raw/voice/AudioWAV \
  --out data/raw/stt/transcripts.jsonl \
  --language en \
  --by-sentence-code \
  --samples-per-code 2 \
  --overwrite
```

## 2) Build manifest (CSV)

```bash
python scripts/stt/build_manifest.py \
  --transcripts data/raw/stt/transcripts.jsonl \
  --out data/raw/stt/manifest.csv \
  --normalize
```

## 3) Split train/val/test

```bash
python scripts/stt/split_manifest.py \
  --manifest data/raw/stt/manifest.csv \
  --seed 42 \
  --group-by speaker_id
```

## 4) Validate manifest

```bash
python scripts/stt/validate_manifest.py \
  --manifest data/raw/stt/manifest.csv
```

## 5) Evaluate WER/CER (offline)

```bash
python scripts/stt/evaluate_stt.py \
  --manifest data/raw/stt/manifest.with_splits.csv \
  --split test \
  --limit 100
```

Fast full-dataset evaluation (CREMA-D sentence codes):

```bash
python scripts/stt/evaluate_stt.py \
  --manifest data/raw/stt/manifest.with_splits.csv \
  --split all \
  --normalize \
  --by-sentence-code \
  --samples-per-code 2
```

## 6) Fine-tune Whisper (optional)

```bash
python scripts/stt/train_whisper.py \
  --train-manifest data/raw/stt/manifest.train.csv \
  --val-manifest data/raw/stt/manifest.val.csv \
  --model openai/whisper-small \
  --epochs 3 \
  --normalize \
  --augment
```

Notes:
- Install optional deps: `pip install -r requirements-optional.txt`
- `faster-whisper` needs `ffmpeg` installed on your machine for non-wav files.
