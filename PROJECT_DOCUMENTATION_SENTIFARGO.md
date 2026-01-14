# Sentifargo (Sentifargo)
## Complete Project Documentation

**Author:** Pratik Niroula  
**Project:** CIS 380 - Machine Learning & Anomaly Detection  
**Last Updated:** January 2026

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Directory Structure](#directory-structure)
3. [Core Components](#core-components)
4. [How Each Module Works](#how-each-module-works)
5. [Running the Project](#running-the-project)
6. [API Endpoints](#api-endpoints)
7. [File-by-File Documentation](#file-by-file-documentation)

---

## 🎯 Project Overview

### What is Sentifargo?

Sentifargo (Sentifargo) is a **multi-modal machine learning platform** that detects various types of anomalies:

| Module | What It Detects | Use Case |
|--------|-----------------|----------|
| **Fraud** | Financial fraud | Credit card transactions, payment anomalies |
| **Cyber** | Network intrusions | Malicious traffic, DDoS attacks |
| **Behavior** | Insider threats | Unusual user activity patterns |
| **Vision** | Fake images | Deepfakes, manipulated photos |
| **NLP** | Text anomalies | Spam, malicious content |
| **Voice** | Audio emotions | Sentiment in voice recordings |

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                          │
│                     ui-web/frontend/src/                         │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                             │
│                        app/main.py                               │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐      │
│  │  /fraud  │  /cyber  │ /behavior│ /vision  │   /rag   │      │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘      │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ML MODELS (src/uais/)                        │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐      │
│  │  XGBoost │ RandomF  │   LSTM   │   CNN    │  BERT    │      │
│  │  (Fraud) │ (Cyber)  │(Behavior)│ (Vision) │  (NLP)   │      │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Directory Structure

```
Sentifargo/
│
├── app/                          # FastAPI application
│   ├── main.py                   # 🔑 Main entry point - starts the API server
│   ├── api/                      # API route handlers
│   │   ├── risk.py              # Unified risk scoring endpoint
│   │   ├── voice.py             # Voice emotion analysis
│   │   ├── brand.py             # Brand/logo detection
│   │   └── ...
│   ├── core/                     # Core utilities
│   │   ├── config.py            # Configuration management
│   │   ├── logging.py           # Logging setup
│   │   └── health.py            # Health check endpoints
│   ├── legacy/                   # Original API implementation
│   │   └── api/routes/          # Route handlers for each ML service
│   │       ├── fraud.py         # /fraud endpoints
│   │       ├── cyber.py         # /cyber endpoints
│   │       ├── behavior.py      # /behavior endpoints
│   │       └── vision.py        # /vision endpoints
│   └── streamlit_chatbot/        # Streamlit UI (alternative frontend)
│       ├── app.py               # Streamlit main app
│       └── pages/               # Streamlit pages
│
├── src/                          # Source code for ML models
│   └── uais/                    # Sentifargo
│       ├── anomaly/             # Anomaly detection algorithms
│       │   ├── isolation_forest.py   # Isolation Forest algorithm
│       │   ├── autoencoder.py        # Autoencoder for anomalies
│       │   └── one_class_svm.py      # One-Class SVM
│       ├── supervised/          # Supervised learning models
│       │   ├── xgboost_model.py      # XGBoost classifier
│       │   ├── random_forest.py      # Random Forest classifier
│       │   └── neural_network.py     # Deep neural network
│       ├── vision/              # Computer vision models
│       │   ├── cnn_classifier.py     # CNN for image classification
│       │   ├── fake_detector.py      # Deepfake detection
│       │   └── yolo_detector.py      # Object detection
│       ├── nlp/                 # Natural language processing
│       │   ├── text_classifier.py    # Text classification
│       │   └── sentiment.py          # Sentiment analysis
│       ├── fusion/              # Model fusion/ensemble
│       │   ├── ensemble.py           # Combine multiple models
│       │   └── voting.py             # Voting classifier
│       └── utils/               # Utility functions
│           ├── metrics.py            # Evaluation metrics
│           └── preprocessing.py      # Data preprocessing
│
├── models/                       # Trained model files (.pkl, .pt, .h5)
│   ├── fraud/                   # Fraud detection models
│   ├── cyber/                   # Cybersecurity models
│   ├── behavior/                # Behavior analysis models
│   └── vision/                  # Vision models
│
├── data/                         # Datasets
│   ├── raw/                     # Original datasets
│   ├── processed/               # Cleaned/processed data
│   └── embeddings/              # Vector embeddings
│
├── config/                       # Configuration files
│   ├── base_config.yaml         # Base settings
│   ├── fraud_config.yaml        # Fraud model settings
│   └── vision_config.yaml       # Vision model settings
│
├── ui-web/                       # React frontend
│   └── frontend/
│       ├── src/
│       │   ├── pages/           # React pages (Home, CommandCenter)
│       │   ├── components/      # React components (Sidebar, Footer)
│       │   └── App.tsx          # Main React app
│       └── dist/                # Built frontend (served by FastAPI)
│
├── notebooks/                    # Jupyter notebooks for experiments
│   ├── 10_supervised_fraud.ipynb
│   └── 20_unsupervised_fraud.ipynb
│
├── tests/                        # Unit tests
├── scripts/                      # Utility scripts
├── docs/                         # GitHub Pages deployment
│
├── requirements.txt              # Python dependencies
├── pyproject.toml               # Project metadata
├── Dockerfile                   # Docker container config
└── docker-compose.yml           # Docker compose config
```

---

## 🔧 Core Components

### 1. FastAPI Backend (`app/main.py`)

The main entry point that:
- Creates the web server
- Registers API routes for each ML service
- Serves the React frontend
- Handles CORS and authentication

```python
# Start the server
uvicorn app.main:app --reload --port 8000
```

### 2. ML Models (`src/uais/`)

Each domain has its own model implementations:

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `anomaly/` | Unsupervised anomaly detection | `isolation_forest.py`, `autoencoder.py` |
| `supervised/` | Classification models | `xgboost_model.py`, `random_forest.py` |
| `vision/` | Image analysis | `cnn_classifier.py`, `fake_detector.py` |
| `nlp/` | Text processing | `text_classifier.py`, `sentiment.py` |
| `fusion/` | Combine multiple models | `ensemble.py` |

### 3. API Routes (`app/legacy/api/routes/`)

Each route handles a specific ML service:

| Route | Endpoint | Function |
|-------|----------|----------|
| `fraud.py` | `/fraud/predict` | Predict if transaction is fraudulent |
| `cyber.py` | `/cyber/predict` | Detect network intrusions |
| `behavior.py` | `/behavior/predict` | Analyze user behavior |
| `vision.py` | `/vision/classify` | Classify images |

### 4. React Frontend (`ui-web/frontend/`)

A modern web interface with:
- **Home Page**: Project overview and stats
- **Command Center**: Interactive ML demo

---

## 🔬 How Each Module Works

### Fraud Detection

```
Input: Transaction data (amount, time, location, merchant)
    │
    ▼
┌─────────────────────────────────────┐
│  Feature Engineering                 │
│  - Normalize amounts                 │
│  - Extract time features             │
│  - Calculate velocity features       │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  XGBoost Classifier                  │
│  - Trained on labeled fraud data     │
│  - Outputs probability 0-1           │
└─────────────────────────────────────┘
    │
    ▼
Output: {is_fraud: true/false, confidence: 0.95}
```

### Vision (Fake/Real Image Detection)

```
Input: Image file
    │
    ▼
┌─────────────────────────────────────┐
│  Preprocessing                       │
│  - Resize to 224x224                 │
│  - Normalize pixel values            │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  CNN Model (ResNet/EfficientNet)     │
│  - Extract visual features           │
│  - Classify as real/fake             │
└─────────────────────────────────────┘
    │
    ▼
Output: {label: "REAL", confidence: 0.87}
```

### Cyber (Network Intrusion Detection)

```
Input: Network traffic data (packets, ports, protocols)
    │
    ▼
┌─────────────────────────────────────┐
│  Feature Extraction                  │
│  - Packet statistics                 │
│  - Connection patterns               │
│  - Protocol analysis                 │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  Ensemble Model                      │
│  - Random Forest + XGBoost           │
│  - Voting for final decision         │
└─────────────────────────────────────┘
    │
    ▼
Output: {attack_type: "DDoS", confidence: 0.92}
```

---

## 🚀 Running the Project

### Quick Start

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Start the backend server
uvicorn app.main:app --reload --port 8000

# 3. Open in browser
# API Docs: http://localhost:8000/docs
# Frontend: http://localhost:8000/ui
```

### Development Mode

```bash
# Backend (with auto-reload)
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd ui-web/frontend
npm run dev
```

### Production Deployment

```bash
# Using Docker
docker-compose up -d

# Or directly with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Redirect to UI |
| `/api/health` | GET | System health check |
| `/fraud/predict` | POST | Fraud detection |
| `/cyber/predict` | POST | Cyber threat detection |
| `/behavior/predict` | POST | Behavior analysis |
| `/vision/classify` | POST | Image classification |
| `/rag/upload` | POST | Upload document for Q&A |
| `/rag/query` | POST | Ask question about documents |
| `/chat` | POST | Chatbot conversation |

### Example API Call

```bash
# Fraud Detection
curl -X POST http://localhost:8000/fraud/predict \
  -H "Content-Type: application/json" \
  -d '{"amount": 1500, "merchant": "electronics", "time": "02:30"}'

# Response
{
  "is_fraud": true,
  "confidence": 0.87,
  "risk_factors": ["high_amount", "unusual_time"]
}
```

---

## 📝 File-by-File Documentation

### Key Files Explained

| File | Purpose |
|------|---------|
| `app/main.py` | Creates FastAPI app, registers routes, serves frontend |
| `app/core/config.py` | Loads configuration from YAML files and environment |
| `app/legacy/api/routes/fraud.py` | Handles `/fraud/*` endpoints |
| `src/uais/supervised/xgboost_model.py` | XGBoost model wrapper |
| `src/uais/vision/fake_detector.py` | Real/fake image classifier |
| `ui-web/frontend/src/pages/Home.tsx` | Homepage React component |
| `config/base_config.yaml` | Base configuration settings |
| `requirements.txt` | Python package dependencies |

---

## 🎓 For Students/Reviewers

### Understanding the Code Flow

1. **User Request** → React frontend sends HTTP request
2. **FastAPI Route** → `app/legacy/api/routes/*.py` receives request
3. **Model Loading** → Load trained model from `models/` directory
4. **Prediction** → Run inference using `src/uais/` code
5. **Response** → Return JSON result to frontend
6. **Display** → React shows result to user

### Key Concepts Used

- **FastAPI**: Modern Python web framework
- **XGBoost**: Gradient boosting for tabular data
- **PyTorch**: Deep learning for vision/NLP
- **React**: Frontend JavaScript library
- **Docker**: Containerization for deployment

---

**Questions?** Check the `/docs` endpoint for interactive API documentation.
