#!/usr/bin/env bash
# Start FastAPI for SentinelForge (pure HTTP).

set -euo pipefail

uvicorn app.main:app --host 0.0.0.0 --port 8000
