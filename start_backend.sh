#!/bin/bash

echo "🚀 Starting Universal Anomaly Intelligence Backend API..."
echo "ℹ️  This API is ready to connect to your Production (React/Next.js) frontend."

# 1. Check if port 8001 is in use and kill it
if lsof -ti :8001 >/dev/null; then
    echo "Freeing port 8001..."
    lsof -ti :8001 | xargs kill -9
fi

# 2. Start the Backend API
echo "📡 Server listening on http://0.0.0.0:8001"
echo "👉 Point your React app API calls to: http://localhost:8001"
python main.py