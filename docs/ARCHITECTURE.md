# 🏗️ SentinelForge Architecture

**Version:** 2.0  
**Last Updated:** January 8, 2026

---

## 📐 System Architecture Diagram

```
┌────────────────────────────┐
│        Frontend UI         │
│  React (Web) / Streamlit   │
│  ChatGPT-style Interface   │
└─────────────┬──────────────┘
              │ REST / JSON
┌─────────────▼──────────────┐
│        FastAPI API         │
│  Auth • Rate-limit • Logs  │
└─────────────┬──────────────┘
              │
┌─────────────▼──────────────┐
│   Agent / Orchestrator     │
│ Intent • Routing • Memory  │
└─────────────┬──────────────┘
              │
┌─────────────▼────────────────────────────────────────────┐
│                  Model Services Layer                     │
│                                                           │
│ Fraud │ Cyber │ Behavior │ Vision │ Audio │ NLP │ RAG    │
│ (Tab) │ (Seq) │ (Time)   │ (Img/V)│ (STT) │(Text)│       │
└─────────────┬────────────────────────────────────────────┘
              │
┌─────────────▼──────────────┐
│     Multimodal Fusion      │
│ Meta-Model + Rule Engine   │
│ Risk Score + Decision      │
└─────────────┬──────────────┘
              │
┌─────────────▼──────────────┐
│ Monitoring & Explainability│
│ Drift • SHAP • Metrics     │
└─────────────┬──────────────┘
              │
┌─────────────▼──────────────┐
│        MLOps Stack         │
│ MLflow • DVC • Registry    │
│ Auto-Retrain • CI/CD       │
└─────────────┬──────────────┘
              │
┌─────────────▼──────────────┐
│     Infra & Deployment     │
│ Docker • Nginx • Grafana   │
│ Prometheus • Redis         │
└────────────────────────────┘
```

---

## 🗂️ Layer-by-Layer Breakdown

### 1️⃣ Frontend UI Layer

| Component | Technology | Location |
|-----------|------------|----------|
| Web Interface | React + TypeScript + Tailwind | `ui-web/frontend/` |
| Dashboard | Streamlit | `dashboard/app_streamlit.py` |
| Chat Interface | React Chat Component | `ui-web/frontend/src/pages/Chat.tsx` |
| Result Cards | React Component | `ui-web/frontend/src/components/ResultCard.tsx` |
| File Upload | React Component | `ui-web/frontend/src/components/UnifiedUploadBox.tsx` |

**Features:**
- ChatGPT-style conversational interface
- Real-time streaming responses
- Multimodal input (text, images, audio, documents)
- Confidence visualization bars
- SHAP explainability dashboard

---

### 2️⃣ FastAPI API Layer

| Component | Location | Purpose |
|-----------|----------|---------|
| Main App | `app/main.py` | Application entry point |
| Chat Endpoint | `app/api/routes/chat.py` | Conversational API |
| Fraud API | `app/api/routes/fraud.py` | Fraud detection |
| Cyber API | `app/api/cyber_timeline.py` | Cyber security timeline |
| Vision API | `app/api/routes/vision.py` | Image/video analysis |
| Voice API | `app/api/voice.py` | Audio processing |
| RAG API | `app/api/routes/rag.py` | Document retrieval |
| Brand API | `app/api/brand.py` | Brand recognition |

**Features:**
- JWT Authentication
- Rate limiting
- Request logging & tracing
- CORS handling
- OpenAPI documentation

**Endpoints:**
```
POST /api/chat          # Main conversational endpoint
POST /api/fraud/predict # Fraud detection
POST /api/cyber/analyze # Cyber threat analysis
POST /api/vision/detect # Image analysis
POST /api/voice/emotion # Voice emotion recognition
POST /api/rag/query     # Document Q&A
GET  /api/cyber/timeline # Security timeline
```

---

### 3️⃣ Agent / Orchestrator Layer

| Component | Location | Purpose |
|-----------|----------|---------|
| Orchestrator | `app/agent/orchestrator.py` | Main routing logic |
| Policy Engine | `agent/policy.py` | Decision policies |
| Intent Detection | `app/agent/confidence.py` | Intent classification |
| Audit Logger | `app/agent/audit_logger.py` | Request auditing |
| Memory Store | `app/agent/orchestrator.py` | Conversation memory |

**Routing Logic:**
```python
Intent Detection → Route Selection → Service Call → Response Fusion
     ↓                   ↓                ↓              ↓
 confidence.py      policy.py       services/*      multimodal.py
```

**Supported Intents:**
| Intent | Route | Handler |
|--------|-------|---------|
| `fraud_check` | Fraud Service | `_handle_fraud()` |
| `cyber_analyze` | Cyber Service | `_handle_cyber()` |
| `behavior_score` | Behavior Service | `_behavior_score()` |
| `vision_detect` | Vision Service | `_handle_vision()` |
| `voice_emotion` | Voice Service | `_handle_voice()` |
| `recommend` | Recommender | `_handle_recommend()` |
| `rag_query` | RAG Pipeline | `_handle_rag()` |
| `general` | LLM Fallback | `_handle_general()` |

---

### 4️⃣ Model Services Layer

#### Fraud Detection (Tabular)
| Model | Location | Algorithm |
|-------|----------|-----------|
| XGBoost | `models/fraud/supervised/` | Gradient Boosting |
| LightGBM | `models/fraud/supervised/` | Gradient Boosting |
| Isolation Forest | `src/uais/anomaly/` | Anomaly Detection |
| Autoencoder | `models/fraud/unsupervised/` | Neural Anomaly |

#### Cyber Anomaly (Sequential)
| Model | Location | Dataset |
|-------|----------|---------|
| Cyber Classifier | `models/cyber/` | UNSW-NB15 |
| Feature Extractor | `src/uais/features/cyber_features.py` | Network flows |

#### Behavioral Intelligence (Time Series)
| Model | Location | Algorithm |
|-------|----------|-----------|
| LOF Scorer | `models/behavior/` | Local Outlier Factor |
| Behavior Scaler | `models/behavior/` | StandardScaler |

#### Vision Intelligence (Image/Video)
| Model | Location | Purpose |
|-------|----------|---------|
| Face Emotion CNN | `models/vision/` | Facial expression |
| Real/Fake Detector | `models/vision/resnet/` | Deepfake detection |
| YOLO v8 | `yolov8n.pt`, `yolov8s.pt` | Object detection |
| Video LSTM | `app/models/video/video_lstm.py` | Temporal reasoning |

#### Audio Intelligence (STT + Emotion)
| Model | Location | Purpose |
|-------|----------|---------|
| Whisper STT | `app/services/stt/whisper_stt.py` | Speech-to-text |
| Voice Emotion | `app/models/voice/` | Emotion classification |
| Calibration | `app/models/voice/calibration.py` | Confidence calibration |

#### NLP & RAG
| Component | Location | Purpose |
|-----------|----------|---------|
| Embeddings | `app/rag/embed.py` | Text embeddings |
| Vector Store | `app/rag/vector_store.py` | FAISS/ChromaDB |
| Retriever | `app/rag/retriever.py` | Semantic search |
| Chunking | `app/rag/chunking.py` | Document splitting |
| OCR | `app/rag/ocr.py` | PDF/Image extraction |
| Metrics | `app/rag/metrics.py` | MRR, NDCG evaluation |

---

### 5️⃣ Multimodal Fusion Layer

| Component | Location | Purpose |
|-----------|----------|---------|
| Fusion Model | `app/models/fusion/multimodal.py` | Cross-modal fusion |
| Meta Classifier | `app/models/fusion/multimodal.py` | Final decision |
| Rule Engine | `app/services/alert_service.py` | Business rules |

**Fusion Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│                 Multimodal Fusion                        │
├─────────────────────────────────────────────────────────┤
│  Text     Image    Audio    Tabular   Behavior          │
│    │        │        │         │          │             │
│    ▼        ▼        ▼         ▼          ▼             │
│ [Embed]  [CNN]   [Whisper]  [XGB]     [LOF]            │
│    │        │        │         │          │             │
│    └────────┴────────┴─────────┴──────────┘             │
│                      │                                   │
│              [Attention Fusion]                          │
│                      │                                   │
│              [Meta Classifier]                           │
│                      │                                   │
│              Risk Score + Decision                       │
└─────────────────────────────────────────────────────────┘
```

---

### 6️⃣ Monitoring & Explainability Layer

| Component | Location | Purpose |
|-----------|----------|---------|
| Drift Detection | `app/monitoring/drift.py` | Data/model drift |
| SHAP Explainer | `dashboard/components/shap_viz.py` | Feature importance |
| Alert Service | `app/services/alert_service.py` | Real-time alerts |
| Latency Monitor | `app/monitoring/latency.py` | Performance tracking |
| Severity Scoring | `app/monitoring/alerts.py` | Alert prioritization |

**Monitoring Dashboard:**
- Model performance metrics
- Drift detection alerts
- SHAP force plots
- Latency percentiles (P50, P95, P99)
- Real-time WebSocket alerts

---

### 7️⃣ MLOps Stack

| Component | Location | Purpose |
|-----------|----------|---------|
| MLflow Config | `mlflow_config.yaml` | Experiment tracking |
| DVC Config | `.dvc/config`, `dvc.yaml` | Data versioning |
| Model Registry | `app/mlops/registry.py` | Model versioning |
| CI/CD | `.github/workflows/ci.yml` | Automated testing |

**Model Lifecycle:**
```
Training → Validation → Registry → Staging → Production
    │          │           │          │          │
 MLflow     Metrics    registry.py  Canary    Deploy
```

---

### 8️⃣ Infrastructure & Deployment

| Component | Location | Purpose |
|-----------|----------|---------|
| Dockerfile | `Dockerfile` | Container build |
| Docker Compose | `docker-compose.yml` | Multi-service |
| Launch Script | `launch_omnichat.sh` | Startup script |

**Container Services:**
```yaml
services:
  api:        # FastAPI backend (port 8000)
  frontend:   # React/Vite (port 5173)
  dashboard:  # Streamlit (port 8501)
  redis:      # Session cache
  prometheus: # Metrics collection
  grafana:    # Visualization
```

---

## 🔄 Data Flow

### Request Flow
```
User Input
    │
    ▼
┌─────────────┐
│  Frontend   │ ──▶ WebSocket / REST
└─────────────┘
    │
    ▼
┌─────────────┐
│  FastAPI    │ ──▶ Auth, Rate Limit, Log
└─────────────┘
    │
    ▼
┌─────────────┐
│ Orchestrator│ ──▶ Intent Detection
└─────────────┘
    │
    ├──▶ Fraud Service ──▶ XGBoost/SHAP
    ├──▶ Cyber Service ──▶ Timeline/Alert
    ├──▶ Vision Service ──▶ YOLO/CNN
    ├──▶ Voice Service ──▶ Whisper/Emotion
    ├──▶ RAG Service ──▶ Vector Search
    │
    ▼
┌─────────────┐
│   Fusion    │ ──▶ Combine Results
└─────────────┘
    │
    ▼
┌─────────────┐
│  Response   │ ──▶ JSON + Confidence + Explanation
└─────────────┘
```

---

## 📁 Directory Structure

```
universal-anomaly-intelligence-v2/
├── app/                          # Main application
│   ├── main.py                   # FastAPI entry
│   ├── agent/                    # Orchestrator
│   │   ├── orchestrator.py
│   │   ├── confidence.py
│   │   └── audit_logger.py
│   ├── api/                      # API routes
│   │   ├── routes/
│   │   └── cyber_timeline.py
│   ├── models/                   # Model wrappers
│   │   ├── fusion/
│   │   ├── video/
│   │   ├── voice/
│   │   └── recommender/
│   ├── monitoring/               # Observability
│   │   ├── drift.py
│   │   ├── alerts.py
│   │   └── latency.py
│   ├── rag/                      # RAG pipeline
│   │   ├── chunking.py
│   │   ├── retriever.py
│   │   ├── ocr.py
│   │   └── metrics.py
│   ├── services/                 # Business logic
│   │   ├── alert_service.py
│   │   └── stt/
│   ├── mlops/                    # MLOps
│   │   └── registry.py
│   └── data/                     # Data utilities
│       └── fraud_generator.py
├── models/                       # Trained models
│   ├── fraud/
│   ├── cyber/
│   ├── behavior/
│   ├── vision/
│   └── nlp/
├── ui-web/                       # React frontend
│   └── frontend/
│       └── src/
│           ├── components/
│           └── pages/
├── dashboard/                    # Streamlit
│   ├── app_streamlit.py
│   └── components/
├── data/                         # Datasets
├── docs/                         # Documentation
├── tests/                        # Test suite
├── configs/                      # Configuration
├── .dvc/                         # DVC config
├── dvc.yaml                      # DVC pipeline
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## 🚀 Quick Start

### Development
```bash
# Backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Frontend
cd ui-web/frontend && npm run dev

# Dashboard
streamlit run dashboard/app_streamlit.py
```

### Docker
```bash
docker-compose up --build
```

### Endpoints
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173
- **Dashboard**: http://localhost:8501

---

## 📊 Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| API Latency (P95) | < 500ms | ✅ ~350ms |
| Model Inference | < 200ms | ✅ ~150ms |
| Throughput | > 100 RPS | ✅ ~120 RPS |
| Availability | 99.9% | ✅ SLA |

---

*Generated by SentinelForge Architecture Tool v2.0*
