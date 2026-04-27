#!/bin/bash
# Zero-downtime blue/green deploy for the docker-compose target.
#
# Strategy:
#   1. Build the new image tagged with the git SHA.
#   2. Stand the new "target" stack up alongside the active one using a
#      different docker-compose project name.
#   3. Health-check the new stack.
#   4. Reload Caddy so it routes to the new stack (handled by the
#      external_links update + Caddy reload).
#   5. Drain the old stack and stop it.
#
# Rollback: ``./scripts/deploy_bluegreen.sh rollback`` flips Caddy back to
# the previous color if its containers are still up.
#
# Usage:
#   ./scripts/deploy_bluegreen.sh deploy <git-sha>
#   ./scripts/deploy_bluegreen.sh rollback
#   ./scripts/deploy_bluegreen.sh status

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

COMPOSE="docker compose -f docker-compose.production.yml -f docker-compose.caddy.yml"
HEALTH_URL="${HEALTH_URL:-http://localhost:8000/health}"
TIMEOUT="${HEALTH_TIMEOUT:-90}"

ACTIVE_FILE="${ACTIVE_FILE:-/var/lib/sentifargo/active_color}"
mkdir -p "$(dirname "$ACTIVE_FILE")" 2>/dev/null || true

current_color() {
    [ -f "$ACTIVE_FILE" ] && cat "$ACTIVE_FILE" || echo "blue"
}

other_color() {
    [ "$(current_color)" = "blue" ] && echo "green" || echo "blue"
}

require() {
    command -v "$1" >/dev/null 2>&1 || { echo "missing required command: $1" >&2; exit 1; }
}

deploy() {
    local sha="${1:-}"
    if [ -z "$sha" ]; then
        echo "usage: deploy_bluegreen.sh deploy <git-sha>" >&2
        exit 2
    fi
    local target
    target="$(other_color)"
    local active
    active="$(current_color)"
    echo "[deploy] active=$active target=$target sha=$sha"

    echo "[deploy] building image sentifargo:$sha"
    docker build -f Dockerfile.production --target production -t "sentifargo:$sha" .

    echo "[deploy] standing up $target stack (project sentifargo-$target)"
    COMPOSE_PROJECT_NAME="sentifargo-$target" SENTIFARGO_IMAGE="sentifargo:$sha" \
        $COMPOSE up -d --no-deps --build api worker

    echo "[deploy] waiting up to ${TIMEOUT}s for $HEALTH_URL"
    local deadline=$((SECONDS + TIMEOUT))
    until curl -fsS "$HEALTH_URL" >/dev/null 2>&1; do
        if [ $SECONDS -ge $deadline ]; then
            echo "[deploy] health check failed; tearing down $target" >&2
            COMPOSE_PROJECT_NAME="sentifargo-$target" $COMPOSE down
            exit 1
        fi
        sleep 2
    done
    echo "[deploy] $target health OK"

    echo "[deploy] reloading Caddy to point at $target"
    docker exec sentifargo-caddy caddy reload --config /etc/caddy/Caddyfile
    echo "$target" > "$ACTIVE_FILE"

    if [ "$active" != "$target" ]; then
        echo "[deploy] draining $active stack (sleep 10 for in-flight requests)"
        sleep 10
        COMPOSE_PROJECT_NAME="sentifargo-$active" $COMPOSE down
    fi

    echo "[deploy] done. active=$target"
}

rollback() {
    local target
    target="$(other_color)"
    echo "[rollback] flipping back to $target"
    if ! docker ps --format '{{.Names}}' | grep -q "sentifargo-$target-api"; then
        echo "[rollback] $target stack is not running; cannot roll back" >&2
        exit 1
    fi
    docker exec sentifargo-caddy caddy reload --config /etc/caddy/Caddyfile
    echo "$target" > "$ACTIVE_FILE"
    echo "[rollback] active=$target"
}

status() {
    echo "active: $(current_color)"
    docker ps --filter "name=sentifargo-" --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
}

cmd="${1:-status}"
shift || true
case "$cmd" in
    deploy)   require docker; require curl; deploy "$@" ;;
    rollback) require docker; rollback ;;
    status)   require docker; status ;;
    *)        echo "usage: $0 {deploy <sha>|rollback|status}" >&2; exit 2 ;;
esac
