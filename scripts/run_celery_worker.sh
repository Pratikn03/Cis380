#!/usr/bin/env bash
set -euo pipefail

CELERY_LOGLEVEL="${CELERY_LOGLEVEL:-info}"

echo "Starting Celery worker..."
celery -A app.services.async_worker worker --loglevel="${CELERY_LOGLEVEL}"
