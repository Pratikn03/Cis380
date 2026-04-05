#!/bin/bash

echo "🚀 Starting Universal Anomaly Intelligence..."

# 1. Check if port 8001 is in use and kill it (prevents 'Address already in use' errors)
if lsof -ti :8001 >/dev/null; then
    echo "Freeing port 8001..."
    lsof -ti :8001 | xargs kill -9
fi

# 2. Start the Backend API in the background
echo "Starting FastAPI Backend..."
python main.py &
BACKEND_PID=$!

# Wait for backend to spin up
sleep 3

# 3. Start the Streamlit Frontend
echo "Starting Streamlit Frontend..."
streamlit run app.py

# 4. Cleanup: Kill the backend when you stop this script (Ctrl+C)
trap "kill $BACKEND_PID" EXIT
wait