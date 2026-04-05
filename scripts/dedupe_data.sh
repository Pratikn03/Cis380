#!/usr/bin/env bash
set -euo pipefail
ROOTS=${ROOTS:-"data/raw data/processed data"}
echo "Scanning roots: $ROOTS"
python scripts/find_duplicates.py $ROOTS
LATEST_MOVE=$(ls -1t reports/duplicates_move_*.sh 2>/dev/null | head -n 1 || true)
if [ -z "${LATEST_MOVE:-}" ]; then
  echo "No move script created (no duplicates found)."
  exit 0
fi
if [ "${DELETE:-0}" = "1" ]; then
  echo "DELETE=1 -> Moving duplicates into trash using: $LATEST_MOVE"
  bash "$LATEST_MOVE"
  echo "✅ Done. Duplicates moved to: data/_duplicates_trash/<timestamp>/"
else
  echo "SAFE MODE: No files were moved."
  echo "If you want to move duplicates to trash, run:"
  echo "  DELETE=1 bash scripts/dedupe_data.sh"
fi
