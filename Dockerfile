# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/ui-web/frontend

# Copy frontend dependency files
# Using wildcards to copy both package.json and package-lock.json if present
COPY ui-web/frontend/package*.json ./

# Install dependencies and build
RUN npm install
COPY ui-web/frontend/ ./
RUN npm run build

# Stage 2: Python Backend & Runtime
FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

# Install system dependencies
# ffmpeg: for audio/video processing
# libgl1/libglib2.0: for opencv-python
# curl: for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy built frontend assets from builder stage
COPY --from=frontend-builder /app/ui-web/frontend/dist ./ui-web/frontend/dist

# Create directory structure for persistence and logs
RUN mkdir -p data/raw data/processed models logs artifacts

# Create a non-root user for security
RUN addgroup --system appgroup && adduser --system --group appuser
RUN chown -R appuser:appgroup /app
USER appuser

# Expose the API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
