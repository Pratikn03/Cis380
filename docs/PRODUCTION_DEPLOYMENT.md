# OmniChatX Production Deployment Guide

## 🚀 Overview

This guide covers deploying OmniChatX (Universal Anomaly Intelligence System) to production environments with proper security, monitoring, and scalability configurations.

## 📋 Prerequisites

- Docker Engine 20.10+
- Docker Compose v2.0+
- Git
- 16GB+ RAM (recommended)
- NVIDIA GPU (optional, for accelerated inference)
- SSL certificates for your domain

## 🏗️ Architecture

```
                                    ┌─────────────────┐
                                    │   Cloudflare    │
                                    │   (CDN/WAF)     │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │     Nginx       │
                                    │ (Reverse Proxy) │
                                    │    Port 80/443  │
                                    └────────┬────────┘
                         ┌───────────────────┼───────────────────┐
                         │                   │                   │
                ┌────────▼────────┐ ┌────────▼────────┐ ┌───────▼────────┐
                │   FastAPI       │ │   Streamlit     │ │   Prometheus   │
                │   (Backend)     │ │   (Frontend)    │ │   (Metrics)    │
                │   Port 8000     │ │   Port 8501     │ │   Port 9090    │
                └────────┬────────┘ └────────┬────────┘ └───────┬────────┘
                         │                   │                   │
                ┌────────▼───────────────────▼────────┐ ┌───────▼────────┐
                │              Redis                   │ │    Grafana     │
                │           (Cache/Sessions)           │ │   (Dashboards) │
                │             Port 6379                │ │   Port 3000    │
                └──────────────────────────────────────┘ └────────────────┘
```

## 🔧 Quick Start

### 1. Clone and Configure

```bash
# Clone repository
git clone <your-repo-url>
cd universal-anomaly-intelligence-v2

# Create environment file
cp .env.production.example .env

# Edit configuration
nano .env
```

### 2. Configure Environment Variables

Edit `.env` with your values:

```bash
# Core Settings
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=your-super-secret-key-min-32-chars
AUTH_TOKEN=your-api-auth-token-min-32-chars

# CORS (comma-separated origins)
CORS_ORIGINS=https://your-domain.com

# OpenAI (for ChatGPT integration)
OPENAI_API_KEY=sk-your-openai-api-key

# Database
DATABASE_URL=sqlite:///./data/omnichatx.db

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_PASSWORD=your-grafana-password

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### 3. Add SSL Certificates

```bash
# Create SSL directory
mkdir -p deploy/nginx/ssl

# Option A: Use existing certificates
cp /path/to/your/cert.pem deploy/nginx/ssl/
cp /path/to/your/key.pem deploy/nginx/ssl/

# Option B: Generate self-signed (for testing only)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout deploy/nginx/ssl/key.pem \
  -out deploy/nginx/ssl/cert.pem \
  -subj "/CN=localhost"

# Option C: Use Let's Encrypt (recommended for production)
certbot certonly --standalone -d your-domain.com
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem deploy/nginx/ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem deploy/nginx/ssl/key.pem
```

### 4. Deploy

```bash
# Make deploy script executable
chmod +x scripts/deploy.sh

# Full deployment
./scripts/deploy.sh deploy

# Or use Docker Compose directly
docker-compose -f docker-compose.production.yml up -d
```

## 🔒 Security Configuration

### Bearer Token Authentication (AUTH_TOKEN)

If `AUTH_TOKEN` is set, all `/api/*` routes require:

`Authorization: Bearer <AUTH_TOKEN>`

```python
import requests

headers = {
    "Authorization": "Bearer your-auth-token",
    "Content-Type": "application/json"
}

response = requests.post(
    "https://your-domain.com/api/chat",
    headers=headers,
    json={"message": "Hello"}
)
```

### Rate Limiting

Default rate limits:
- **API endpoints**: 100 requests/minute per IP
- **Chat endpoints**: 30 requests/minute per user
- **Upload endpoints**: 10 requests/minute per user

### CORS Configuration

Edit `nginx.conf` to update allowed origins:

```nginx
# In nginx.conf
add_header 'Access-Control-Allow-Origin' 'https://your-allowed-domain.com';
```

## 📊 Monitoring

### Prometheus Metrics

Access at: `https://your-domain.com:9090`

Key metrics:
- `omnichatx_requests_total` - Total HTTP requests
- `omnichatx_request_duration_seconds` - Request latency
- `omnichatx_active_connections` - Current connections
- `omnichatx_model_inference_duration` - ML model latency

### Grafana Dashboards

Access at: `https://your-domain.com:3000`

Default login:
- Username: `admin`
- Password: (set in .env.production)

Pre-configured dashboards:
- **OmniChatX Overview** - High-level system metrics
- **API Performance** - Request/response analysis
- **Model Inference** - ML model performance
- **Error Analysis** - Error rates and types

### Health Checks

```bash
# Basic health
curl https://your-domain.com/health

# Kubernetes liveness
curl https://your-domain.com/health/live

# Kubernetes readiness
curl https://your-domain.com/health/ready

# Detailed health with component status
curl https://your-domain.com/health/detailed
```

## 🔄 Operations

### Viewing Logs

```bash
# All services
docker-compose -f docker-compose.production.yml logs -f

# Specific service
docker-compose -f docker-compose.production.yml logs -f omnichatx-api

# Last 100 lines
docker-compose -f docker-compose.production.yml logs --tail=100 omnichatx-api
```

### Scaling Services

```bash
# Scale API to 3 instances
docker-compose -f docker-compose.production.yml up -d --scale omnichatx-api=3

# Note: Ensure load balancing is configured in nginx
```

### Updating Deployment

```bash
# Pull latest code
git pull origin main

# Rebuild and redeploy
./scripts/deploy.sh deploy

# Or with zero downtime
./scripts/deploy.sh deploy  # Handles rolling updates
```

### Backup & Restore

```bash
# Backup Redis data
docker-compose -f docker-compose.production.yml exec redis redis-cli BGSAVE

# Backup volumes
docker run --rm -v omnichatx-redis-data:/data -v $(pwd):/backup alpine \
  tar czf /backup/redis_backup.tar.gz /data

# Restore
docker run --rm -v omnichatx-redis-data:/data -v $(pwd):/backup alpine \
  tar xzf /backup/redis_backup.tar.gz -C /
```

## 🐛 Troubleshooting

### Common Issues

#### Container won't start

```bash
# Check logs
docker-compose -f docker-compose.production.yml logs omnichatx-api

# Check resource usage
docker stats

# Verify network
docker network ls
docker network inspect omnichatx-network
```

#### High memory usage

```bash
# Check memory per container
docker stats --no-stream

# Reduce workers if needed (edit docker-compose.production.yml)
# environment:
#   - WORKERS=2
```

#### SSL issues

```bash
# Test SSL certificates
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Verify certificate dates
openssl x509 -in deploy/nginx/ssl/cert.pem -noout -dates
```

#### API returning 502

```bash
# Check if backend is running
docker-compose -f docker-compose.production.yml ps

# Check nginx upstream configuration
docker-compose -f docker-compose.production.yml exec nginx nginx -t
```

### Debug Mode

For temporary debugging (NOT for production):

```bash
# Enable debug mode
docker-compose -f docker-compose.production.yml exec omnichatx-api \
  /bin/bash -c "DEBUG=true python -m app.main"
```

## 📈 Performance Tuning

### API Workers

Edit `docker-compose.production.yml`:

```yaml
omnichatx-api:
  environment:
    - WORKERS=4  # CPU cores * 2 + 1
    - TIMEOUT=120
```

### Redis Configuration

For high-traffic scenarios:

```yaml
redis:
  command: >
    redis-server 
    --maxmemory 2gb
    --maxmemory-policy allkeys-lru
    --save ""
    --appendonly no
```

### Nginx Optimization

Edit `deploy/nginx/nginx.conf`:

```nginx
# Increase worker connections
events {
    worker_connections 4096;
}

# Enable caching
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g;
```

## 🔄 CI/CD Pipeline

GitHub Actions workflow is configured in `.github/workflows/ci-cd.yml`:

1. **On Push to main**: 
   - Run tests
   - Build Docker image
   - Push to registry
   - Deploy to staging

2. **On Tag (v*)**:
   - Run full test suite
   - Build production image
   - Push to registry
   - Deploy to production

### Manual Deployment

```bash
# Trigger deployment via GitHub CLI
gh workflow run ci-cd.yml -f environment=production
```

## 📝 API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `https://your-domain.com/docs`
- **ReDoc**: `https://your-domain.com/redoc`

## 🆘 Support

For issues:
1. Check logs: `docker-compose logs`
2. Review health: `curl /health/detailed`
3. Check metrics: Grafana dashboards
4. Open GitHub issue with:
   - Error logs
   - Environment info
   - Steps to reproduce

---

## Quick Reference Commands

```bash
# Start
./scripts/deploy.sh deploy

# Stop
./scripts/deploy.sh stop

# Restart
./scripts/deploy.sh restart

# Status
./scripts/deploy.sh status

# Logs
./scripts/deploy.sh logs

# Update
git pull && ./scripts/deploy.sh deploy

# Clean everything
./scripts/deploy.sh clean
```
