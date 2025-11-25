# UAIS-V Dockerfile
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y git build-essential && rm -rf /var/lib/apt/lists/*

# Copy code
COPY . /app

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose ports for API and Dashboard
EXPOSE 8501 8000 5000

# Default command (can override)
CMD ["bash"]
