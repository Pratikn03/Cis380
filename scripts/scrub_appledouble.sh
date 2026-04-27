#!/bin/bash
# Removes macOS AppleDouble (`._*`) ghost files. The external drive that hosts
# this repo periodically writes resource-fork copies that pip / matplotlib /
# pygments interpret as broken distributions or undecodable config files.
#
# Run this when:
#   - pip prints "Ignoring invalid distribution -<pkgname>" warnings.
#   - matplotlib / pygments raise "'utf-8' codec can't decode byte ..." on import.
#   - You moved or copied this directory between filesystems.
#
# Usage:
#   bash scripts/scrub_appledouble.sh [path...]
#
# Default scrub targets are .venv/, ui-web/frontend/node_modules/, and the repo
# root. Pass explicit paths to override.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGETS=("$@")
if [ "${#TARGETS[@]}" -eq 0 ]; then
    TARGETS=(
        "${ROOT}/.venv"
        "${ROOT}/ui-web/frontend/node_modules"
        "${ROOT}"
    )
fi

total=0
for target in "${TARGETS[@]}"; do
    if [ ! -e "$target" ]; then
        continue
    fi
    count=$(find "$target" -name "._*" -type f 2>/dev/null | wc -l | tr -d ' ')
    if [ "$count" -gt 0 ]; then
        find "$target" -name "._*" -type f -delete 2>/dev/null || true
        echo "Scrubbed $count AppleDouble files from $target"
        total=$((total + count))
    fi
done

echo "Total removed: $total"
echo "Tip: export COPYFILE_DISABLE=1 in your shell profile to suppress new ones."
