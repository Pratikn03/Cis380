# OmniChatX User Guide

## Overview
OmniChatX is a comprehensive AI assistant that combines multiple capabilities:
- **Chat**: Conversational AI for general questions
- **Fraud Detection**: Analyze transactions for fraudulent patterns
- **Cyber Security**: Detect network intrusion and threats
- **Behavior Analysis**: Identify anomalous user behavior
- **Vision Analysis**: Image classification and object detection
- **Voice Emotion**: Detect emotions from audio
- **RAG Search**: Search through uploaded documents

## How to Use Each Feature

### 💬 Chat Assistant
Simply type your question in the chat box. The AI will respond using:
- Local document knowledge (RAG)
- OpenAI GPT (if API key is configured)
- Built-in offline responses

**Example prompts:**
- "What is machine learning?"
- "How do I detect fraud?"
- "Explain cybersecurity best practices"

### 💳 Fraud Detection
To analyze fraud risk, include transaction data in your message:
- "Check fraud risk: amount=5000, merchant=online, time=2am"
- "Analyze transaction 1000 50.5 3 online"
- Numbers are mapped to fraud model features

**Risk Levels:**
- 🟢 LOW: Score < 0.4
- 🟡 MEDIUM: Score 0.4-0.7
- 🔴 HIGH: Score > 0.7

### 🔐 Cyber Security Analysis
For network intrusion detection:
- "Check cyber threat: 192.168.1.1 443 1000 bytes"
- Include numeric network features for analysis

### 🎭 Behavior Profiling
Detect anomalous user behavior patterns:
- "Analyze behavior: login_count=50, session_time=3600"
- Uses Local Outlier Factor (LOF) algorithm

### 📷 Vision Analysis
Upload an image to get:
- Image classification (what's in the image)
- Object detection results
- Confidence scores

**Supported formats:** PNG, JPG, JPEG, WebP

### 🎤 Voice Emotion Detection
Upload audio to detect emotions:
- Happy, Sad, Angry, Fear, Neutral, Surprise, Disgust
- Confidence percentage for each prediction

**Supported formats:** WAV, MP3, M4A, OGG

### 📚 Document Search (RAG)
Upload documents to the `data/docs/` folder, then ask questions:
- "Search docs: machine learning basics"
- "What does the documentation say about fraud?"

## Tips for Best Results

1. **Be specific**: More details = better responses
2. **Use the right format**: Include numbers for ML models
3. **Enable features**: Toggle features in sidebar as needed
4. **Check attachments**: Verify files uploaded successfully

## Troubleshooting

### "Model not available"
Some models need training first:
```bash
python scripts/train_all.py --with-vision
```

### "Offline mode"
Set `OPENAI_API_KEY` environment variable for GPT responses.

### Slow responses
- Vision/audio processing takes time
- Large files are processed in chunks
- First request loads models (slower)
