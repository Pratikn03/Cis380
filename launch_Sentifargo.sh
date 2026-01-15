#!/bin/bash
# Launch Sentifargo Streamlit UI (Command Center)

echo "🧠 Starting Sentifargo - Streamlit Command Center"
echo "=================================================="
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "✅ Activating virtual environment..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "✅ Activating virtual environment..."
    source venv/bin/activate
fi

# Set backend URL
export Sentifargo_BACKEND=${Sentifargo_BACKEND:-"http://localhost:8000"}
echo "🔗 Backend URL: $Sentifargo_BACKEND"
echo ""

# Launch Streamlit
echo "🚀 Launching Streamlit interface..."
echo "📱 Access the app at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

streamlit run app/streamlit_chatbot/app.py \
    --server.port=8501 \
    --server.headless=true \
    --browser.serverAddress=localhost \
    --theme.base=dark \
    --theme.primaryColor="#3b82f6" \
    --theme.backgroundColor="#1a252f" \
    --theme.secondaryBackgroundColor="#1e3a5f"
