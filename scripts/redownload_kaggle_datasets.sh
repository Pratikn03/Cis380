#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KAGGLE_BIN="${KAGGLE_BIN:-kaggle}"
FORCE="${FORCE:-0}"

# Toggle downloads (1 = download, 0 = skip).
DOWNLOAD_FRAUD="${DOWNLOAD_FRAUD:-1}"
DOWNLOAD_MOVIELENS="${DOWNLOAD_MOVIELENS:-1}"
DOWNLOAD_DAGM="${DOWNLOAD_DAGM:-1}"
DOWNLOAD_FER2013="${DOWNLOAD_FER2013:-0}"

# Optional dataset IDs (set to enable).
UNSW_DATASET="${UNSW_DATASET:-}"

log() {
  printf "\n[%s] %s\n" "$(date +%H:%M:%S)" "$*"
}

require_kaggle() {
  if ! command -v "$KAGGLE_BIN" >/dev/null 2>&1; then
    echo "ERROR: Kaggle CLI not found. Install with: pip install kaggle" >&2
    exit 1
  fi
  if [[ ! -f "${HOME}/.kaggle/kaggle.json" ]]; then
    echo "ERROR: Missing ~/.kaggle/kaggle.json (Kaggle API token)." >&2
    exit 1
  fi
}

download_dataset() {
  local dataset_id="$1"
  local dest_dir="$2"
  local expected_path="$3"

  mkdir -p "$dest_dir"
  if [[ "$FORCE" -ne 1 && -n "$expected_path" && -e "$expected_path" ]]; then
    log "Skip (exists): $expected_path"
    return 0
  fi
  log "Downloading dataset: $dataset_id"
  "$KAGGLE_BIN" datasets download -d "$dataset_id" -p "$dest_dir" --unzip
}

download_competition() {
  local comp_name="$1"
  local dest_dir="$2"
  local expected_path="$3"

  mkdir -p "$dest_dir"
  if [[ "$FORCE" -ne 1 && -n "$expected_path" && -e "$expected_path" ]]; then
    log "Skip (exists): $expected_path"
    return 0
  fi
  log "Downloading competition: $comp_name"
  "$KAGGLE_BIN" competitions download -c "$comp_name" -p "$dest_dir"
  log "Downloaded to: $dest_dir (unzip manually if needed)"
}

require_kaggle

if [[ "$DOWNLOAD_FRAUD" -eq 1 ]]; then
  download_dataset \
    "mlg-ulb/creditcardfraud" \
    "$ROOT/data/raw/fraud" \
    "$ROOT/data/raw/fraud/creditcard.csv"
fi

if [[ "$DOWNLOAD_MOVIELENS" -eq 1 ]]; then
  if [[ "$FORCE" -ne 1 && -f "$ROOT/data/raw/recommendation/movielens.csv" ]]; then
    log "Skip (exists): $ROOT/data/raw/recommendation/movielens.csv"
  else
    log "Downloading MovieLens via helper script"
    python "$ROOT/scripts/download_movielens.py"
  fi
fi

if [[ "$DOWNLOAD_DAGM" -eq 1 ]]; then
  if [[ "$FORCE" -ne 1 && -d "$ROOT/dataset/images/train" ]]; then
    log "Skip (exists): $ROOT/dataset/images/train"
  else
    log "Downloading DAGM 2007 via helper script"
    python "$ROOT/download_kaggle_data.py"
  fi
fi

if [[ -n "$UNSW_DATASET" ]]; then
  download_dataset \
    "$UNSW_DATASET" \
    "$ROOT/data/raw/cyber" \
    "$ROOT/data/raw/cyber/UNSW_NB15_training-set.csv"
else
  log "Skip UNSW-NB15 (set UNSW_DATASET=<kaggle-dataset-id> to enable)"
fi

if [[ "$DOWNLOAD_FER2013" -eq 1 ]]; then
  download_competition \
    "challenges-in-representation-learning-facial-expression-recognition-challenge" \
    "$ROOT/data/raw/vision/face_emotion/_kaggle" \
    "$ROOT/data/raw/vision/face_emotion/_kaggle/train.csv"
fi

log "Done."
