# 🚀 OmniChatX Production Deployment Guide

## Overview

This guide covers deploying OmniChatX to production with enterprise-grade features:
- Multi-stage Docker builds
- Health checks & monitoring
- Rate limiting & security
- CI/CD pipeline
- Logging & metrics

## Quick Start

```bash
# 1. Copy and configure environment
cp .env.production.example .env
# Edit .env with your settings

# 2. Deploy
./scripts/deploy.sh deploy

# 3. Check status
./scripts/deploy.sh status
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx (Reverse Proxy)                │
│                    SSL Termination, Rate Limiting           │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│  OmniChatX    │ │  OmniChatX    │ │  Streamlit    │
│  API (8000)   │ │  API (8000)   │ │  UI (8501)    │
│  (Worker 1)   │ │  (Worker N)   │ │               │
└───────┬───────┘ └───────┬───────┘ └───────────────┘
        │                 │
        └────────┬────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌───────────────┐ ┌───────────────┐
│     Redis     │ │   ML Models   │
│    (Cache)    │ │   (Storage)   │
└───────────────┘ └───────────────┘
        │
        ▼
┌───────────────────────────────────┐
│          Prometheus + Grafana      │
│            (Monitoring)            │
└───────────────────────────────────┘
```

## Deployment Options

### Option 1: Docker Compose (Recommended)

```bash
# Basic deployment (API + UI + Redis)
docker compose -f docker-compose.production.yml up -d

# With monitoring (+ Prometheus + Grafana)
docker compose -f docker-compose.production.yml --profile monitoring up -d

# Full production (+ Nginx reverse proxy)
docker compose -f docker-compose.production.yml --profile monitoring --profile production up -d
```

### Option 2: Kubernetes

```bash
# Apply Kubernetes manifests
kubectl apply -f deploy/k8s/

# Or use Helm
helm install omnichatx ./deploy/helm/omnichatx
```

### Option 3: Cloud Platforms

**AWS ECS:**
```bash
aws ecs update-service --cluster omnichatx --service api --force-new-deployment
```

**Google Cloud Run:**
```bash
gcloud run deploy omnichatx-api \
  --image gcr.io/PROJECT/omnichatx:latest \
  --platform managed \
  --region us-central1
```

**Azure Container Apps:**
```bash
az containerapp update --name omnichatx-api --resource-group rg-omnichatx
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment (development/staging/production) | development |
| `API_PORT` | API server port | 8000 |
| `UI_PORT` | Streamlit UI port | 8501 |
| `SECRET_KEY` | Application secret key | (generate) |
| `AUTH_TOKEN` | API authentication token | (none) |
| `CORS_ORIGINS` | Allowed CORS origins | * |
| `DATABASE_URL` | Database connection URL | sqlite:///./data/omnichatx.db |
| `REDIS_URL` | Redis connection URL | redis://localhost:6379/0 |
| `OPENAI_API_KEY` | OpenAI API key | (none) |
| `LOG_LEVEL` | Logging level | INFO |

### Security Configuration

```bash
# Generate secure secret key
openssl rand -hex 32

# Generate auth token
openssl rand -hex 16
```

**Recommended `.env` for production:**
```bash
APP_ENV=production
DEBUG=false
SECRET_KEY=<generated-key>
AUTH_TOKEN=<generated-token>
CORS_ORIGINS=https://yourdomain.com
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

## Health Checks

### Endpoints

| Endpoint | Purpose | Response |
|----------|---------|----------|
| `/health` | Quick health check | `{"status": "healthy"}` |
| `/health/live` | Kubernetes liveness | `{"status": "alive"}` |
| `/health/ready` | Kubernetes readiness | Detailed component status |
| `/health/detailed` | Full system health | All components + system info |
| `/metrics` | Prometheus metrics | Prometheus format |

### Health Check Response

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "timestamp": "2025-12-17T12:00:00Z",
  "components": [
    {"name": "database", "status": "healthy", "latency_ms": 5.2},
    {"name": "redis", "status": "healthy", "latency_ms": 1.1},
    {"name": "models", "status": "healthy", "latency_ms": 0.5},
    {"name": "disk", "status": "healthy", "latency_ms": 0.3},
    {"name": "memory", "status": "healthy", "latency_ms": 0.2}
  ]
}
```

## Monitoring

### Prometheus Metrics

Available metrics:
- `omnichatx_requests_total` - Total HTTP requests
- `omnichatx_request_duration_seconds` - Request latency
- `omnichatx_model_inference_total` - Model inferences
- `omnichatx_model_inference_seconds` - Model latency
- `omnichatx_model_errors_total` - Model errors
- `omnichatx_health_check_status` - Health check status
- `omnichatx_memory_usage_bytes` - Memory usage

### Grafana Dashboards

1. **API Performance** - Request rates, latencies, errors
2. **Model Performance** - Inference times, throughput
3. **System Health** - CPU, memory, disk
4. **Business Metrics** - Usage patterns

Access Grafana at: http://localhost:3000 (default: admin/admin)

## Security

### Rate Limiting

Default: 100 requests per minute per IP

```python
# Configure in .env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### Authentication

API requests require `Authorization` header:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.example.com/api/chat
```

### Security Headers

All responses include:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000`
- `Content-Security-Policy: default-src 'none'`

### SSL/TLS

Place certificates in `deploy/nginx/ssl/`:
- `cert.pem` - SSL certificate
- `key.pem` - Private key

For Let's Encrypt:
```bash
certbot certonly --webroot -w /var/www/certbot -d yourdomain.com
```

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.production.yml
omnichatx-api:
  deploy:
    replicas: 4
    resources:
      limits:
        cpus: '4'
        memory: 8G
```

### Load Balancing

Nginx upstream configuration in `deploy/nginx/nginx.conf`:
```nginx
upstream omnichatx_api {
    least_conn;
    server omnichatx-api-1:8000;
    server omnichatx-api-2:8000;
    server omnichatx-api-3:8000;
}
```

### Auto-Scaling (Kubernetes)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: omnichatx-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: omnichatx-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Backup & Recovery

### Backup Data

```bash
./scripts/deploy.sh backup
```

Creates backup in `backups/backup_YYYYMMDD_HHMMSS.tar.gz`:
- Data directory
- Configuration files
- Docker volumes

### Restore

```bash
./scripts/deploy.sh restore backups/backup_20251217_120000.tar.gz
```

### Database Backup (PostgreSQL)

```bash
pg_dump -h localhost -U user omnichatx > backup.sql
psql -h localhost -U user omnichatx < backup.sql
```

## CI/CD Pipeline

### GitHub Actions

The `.github/workflows/ci-cd.yml` pipeline:

1. **Lint** - Ruff, Black, MyPy
2. **Test** - Pytest with coverage
3. **Security** - Trivy vulnerability scan
4. **Build** - Docker image build
5. **Deploy Staging** - Auto-deploy to staging (develop branch)
6. **Deploy Production** - Manual deploy on release

### Manual Deployment

```bash
# Build and push image
docker build -t ghcr.io/owner/omnichatx:v1.0.0 -f Dockerfile.production .
docker push ghcr.io/owner/omnichatx:v1.0.0

# Deploy
./scripts/deploy.sh deploy -p production
```

## Troubleshooting

### Common Issues

**Container won't start:**
```bash
docker compose -f docker-compose.production.yml logs omnichatx-api
```

**Health check failing:**
```bash
curl -v http://localhost:8000/health/detailed
```

**High memory usage:**
```bash
docker stats omnichatx-api
```

**Model loading errors:**
```bash
docker exec omnichatx-api ls -la /app/models/
```

### Logs

```bash
# All logs
./scripts/deploy.sh logs

# Follow logs
./scripts/deploy.sh logs -f

# Specific service
docker logs omnichatx-api -f
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DEBUG=true
./scripts/deploy.sh restart
```

## Performance Tuning

### Gunicorn Workers

```bash
# Formula: (2 x CPU cores) + 1
WORKERS=9  # For 4-core machine
```

### Redis Caching

```python
# Cache TTL in seconds
CACHE_TTL=3600
```

### Model Optimization

```bash
# Use quantized models for faster inference
VISION_MODEL=yolov8n  # Nano model
WHISPER_MODEL=tiny    # Tiny model
```

## Maintenance

### Zero-Downtime Deployment

```bash
# Rolling update
docker compose -f docker-compose.production.yml up -d --no-deps --build omnichatx-api
```

### Database Migrations

```bash
docker exec omnichatx-api python -m alembic upgrade head
```

### Clear Cache

```bash
docker exec omnichatx-redis redis-cli FLUSHALL
```

## Support

- **Documentation**: `/docs`
- **API Reference**: `http://localhost:8000/docs`
- **Issues**: GitHub Issues
- **Contact**: support@example.com

---

**Built with ❤️ by Pratik**
