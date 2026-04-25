#!/bin/bash
# ============================================
# Sentifargo Production Deployment Script
# ============================================

set -e  # Exit on error
set -o pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.production.yml"
ENV_FILE="${PROJECT_ROOT}/.env"

ACTION="deploy"

# ============================================
# Helper Functions
# ============================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

usage() {
    cat << EOF
Sentifargo Deployment Script

Usage: $0 [OPTIONS] COMMAND

Commands:
    deploy          Deploy the application (default)
    stop            Stop all services
    restart         Restart all services
    status          Show service status
    logs            Show service logs
    build           Build Docker images
    clean           Remove containers and volumes
    backup          Backup data and configurations
    restore         Restore from backup
    health          Check service health

Options:
    -e, --env-file  Path to environment file (default: .env)
    -h, --help      Show this help message

Examples:
    $0 deploy                    # Deploy the production Docker VM stack
    $0 logs -f                   # Follow logs
    $0 status                    # Check status

EOF
}

check_requirements() {
    log_info "Checking requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check environment file
    if [[ ! -f "$ENV_FILE" ]]; then
        log_warning ".env file not found. Creating from example..."
        if [[ -f "${PROJECT_ROOT}/.env.production.example" ]]; then
            cp "${PROJECT_ROOT}/.env.production.example" "$ENV_FILE"
            log_warning "Please edit $ENV_FILE with your settings"
        else
            log_error "No .env.production.example found"
            exit 1
        fi
    fi
    
    log_success "All requirements met"
}

compose() {
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

build_images() {
    log_info "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    compose build --no-cache
    
    log_success "Images built successfully"
}

deploy() {
    log_info "Deploying Sentifargo production stack"
    
    cd "$PROJECT_ROOT"
    
    # Pull latest images
    log_info "Pulling latest images..."
    compose pull --ignore-buildable || true

    # Start core dependencies first
    log_info "Starting database + cache..."
    compose up -d postgres redis

    # Run migrations before starting the API
    log_info "Running database migrations..."
    compose run --rm migrate

    # Start services
    log_info "Starting services..."
    compose up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 10
    
    # Check health
    check_health
    
    log_success "Deployment complete!"
    show_status
}

stop_services() {
    log_info "Stopping all services..."
    
    cd "$PROJECT_ROOT"
    compose down
    
    log_success "All services stopped"
}

restart_services() {
    log_info "Restarting services..."
    
    stop_services
    deploy
}

show_status() {
    log_info "Service Status:"
    
    cd "$PROJECT_ROOT"
    compose ps
}

show_logs() {
    log_info "Showing logs..."
    
    cd "$PROJECT_ROOT"
    
    # Check for follow flag
    local follow_flag=""
    if [[ "$2" == "-f" ]] || [[ "$2" == "--follow" ]]; then
        follow_flag="-f"
    fi
    
    compose logs $follow_flag
}

clean_up() {
    log_warning "This will remove all containers, volumes, and networks!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Cleaning up..."
        
        cd "$PROJECT_ROOT"
        compose down -v --remove-orphans
        
        # Remove dangling images
        docker image prune -f
        
        log_success "Cleanup complete"
    else
        log_info "Cleanup cancelled"
    fi
}

backup_data() {
    log_info "Creating backup..."
    
    local backup_dir="${PROJECT_ROOT}/backups"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="${backup_dir}/backup_${timestamp}"
    
    mkdir -p "$backup_path"
    
    # Backup data directory
    if [[ -d "${PROJECT_ROOT}/data" ]]; then
        cp -r "${PROJECT_ROOT}/data" "${backup_path}/data"
    fi
    
    # Backup configuration
    cp "${PROJECT_ROOT}/.env" "${backup_path}/.env" 2>/dev/null || true
    
    # Export Docker volumes
    for volume in $(docker volume ls -q | grep Sentifargo); do
        log_info "Backing up volume: $volume"
        docker run --rm -v $volume:/data -v ${backup_path}:/backup alpine \
            tar czf /backup/${volume}.tar.gz -C /data .
    done
    
    # Compress backup
    cd "$backup_dir"
    tar czf "backup_${timestamp}.tar.gz" "backup_${timestamp}"
    rm -rf "backup_${timestamp}"
    
    log_success "Backup created: ${backup_dir}/backup_${timestamp}.tar.gz"
}

check_health() {
    log_info "Checking service health..."
    
    local api_url="${Sentifargo_BACKEND:-http://localhost:8000}"
    local max_retries=30
    local retry=0
    
    while [[ $retry -lt $max_retries ]]; do
        if curl -sf "${api_url}/health/live" > /dev/null 2>&1; then
            if ready_json="$(curl -sf "${api_url}/health/ready" 2>/dev/null)"; then
                if READY_JSON="$ready_json" python3 - <<'PY'
import json
import os
import sys

payload = json.loads(os.environ["READY_JSON"])
components = {item["name"]: item["status"] for item in payload.get("components", [])}
required = ["database", "redis", "worker", "model_manifest", "disk", "memory"]
missing = [name for name in required if components.get(name) != "healthy"]
if payload.get("status") == "unhealthy" or missing:
    print(f"missing required ready components: {', '.join(missing) if missing else 'status=unhealthy'}")
    raise SystemExit(1)
raise SystemExit(0)
PY
                then
                    log_success "API readiness checks passed"
                    if [[ -n "${AUTH_TOKEN:-}" ]]; then
                        curl -s -H "Authorization: Bearer ${AUTH_TOKEN}" "${api_url}/health/detailed" | python3 -m json.tool 2>/dev/null || true
                    fi
                    return 0
                fi
            fi
            log_info "API is live but readiness checks are not yet passing"
        fi
        
        retry=$((retry + 1))
        log_info "Waiting for API to be ready... ($retry/$max_retries)"
        sleep 2
    done
    
    log_error "API health check failed after $max_retries attempts"
    return 1
}

# ============================================
# Main Script
# ============================================

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        deploy|stop|restart|status|logs|build|clean|backup|restore|health)
            ACTION="$1"
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Execute action
case $ACTION in
    deploy)
        check_requirements
        deploy
        ;;
    stop)
        stop_services
        ;;
    restart)
        check_requirements
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$@"
        ;;
    build)
        check_requirements
        build_images
        ;;
    clean)
        clean_up
        ;;
    backup)
        backup_data
        ;;
    health)
        check_health
        ;;
    *)
        usage
        exit 1
        ;;
esac

exit 0
