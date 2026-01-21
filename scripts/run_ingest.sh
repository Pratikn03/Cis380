#!/usr/bin/env bash
set -euo pipefail

echo "[ingest] Building DSA document index"
python scripts/rag/build_index.py
