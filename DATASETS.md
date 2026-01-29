# DATASETS REGISTRY

## Standard Layout
- data/raw/<task>/<dataset>/
- data/processed/<task>/<dataset>/
- data/splits/<task>/<dataset>/splits.json
- data/docs/ (general RAG source)
- data/dsa_docs/ (DSA RAG source)

## Required per dataset
- manifest.json (counts, checksums optional)
- validation report (reports/data_quality/<task>/<dataset>/report.json)

## Template
### <dataset_name>
- Task: tabular|vision|audio|docs
- Source:
- License:
- Raw path:
- Expected structure:
- Labels:
- Split strategy:
- Validation:
  python scripts/data/validate_dataset.py --task <task> --dataset <dataset_name> --path <path>

## Detected dataset roots (current repo)
- data/raw/fraud/creditcard.csv (configs/data_fraud.yaml)
- data/raw/cyber/ (configs/data_cyber.yaml)
- data/raw/behavior/ (configs/data_behavior.yaml)
- data/raw/vision/
- data/raw/brand/
- data/raw/crema_d/ (audio/video source)
- data/raw/voice/ (voice emotion classes)
- data/raw/stt/ (speech-to-text transcripts + manifest)
- data/raw/recommendation/
- data/raw/dsa/

## STT Dataset (Speech Recognition)
- Task: speech-to-text (English)
- Source: bootstrap from local audio (offline Whisper) or add labeled corpora
- Raw audio: `data/raw/voice/AudioWAV` or `data/raw/stt/audio/`
- Transcripts: `data/raw/stt/transcripts.jsonl`
- Manifest: `data/raw/stt/manifest.csv`
- Splits: `data/raw/stt/manifest.{train,val,test}.csv`
