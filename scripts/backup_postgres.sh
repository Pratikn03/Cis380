#!/bin/bash
# Nightly Postgres backup. Designed to run from cron on the host:
#   3 0 * * *  /opt/sentifargo/scripts/backup_postgres.sh >> /var/log/sentifargo-backup.log 2>&1
#
# What it does:
#   1. Runs ``pg_dump --format=custom`` inside the postgres container.
#   2. Writes the dump to ``$BACKUP_DIR`` with an ISO date stamp.
#   3. Tightens permissions to 600 (root-readable only).
#   4. Removes dumps older than ``$RETENTION_DAYS`` (default 30).
#
# Restore:
#   pg_restore --clean --no-owner -d $DATABASE_URL <dump.bin>
#
# Off-site replication: this script is host-local. Wrap with rclone or
# aws s3 sync for off-site retention.

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/sentifargo/postgres}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-sentifargo-postgres}"
POSTGRES_DB="${POSTGRES_DB:-sentifargo}"
POSTGRES_USER="${POSTGRES_USER:-sentifargo}"

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
out="$BACKUP_DIR/sentifargo-${stamp}.bin"

echo "[backup] starting pg_dump → $out"
if ! docker exec -i "$POSTGRES_CONTAINER" \
        pg_dump --username "$POSTGRES_USER" --format=custom --no-owner --no-privileges \
        "$POSTGRES_DB" > "$out"; then
    echo "[backup] pg_dump failed" >&2
    rm -f "$out"
    exit 1
fi
chmod 600 "$out"

size=$(du -h "$out" | cut -f1)
echo "[backup] OK ($size)"

echo "[backup] pruning dumps older than ${RETENTION_DAYS} days"
find "$BACKUP_DIR" -name 'sentifargo-*.bin' -type f -mtime +"$RETENTION_DAYS" -print -delete || true
echo "[backup] done"
