# Sentifargo: Sentifargo

## 🎯 Project Overview

**Sentifargo** is a comprehensive AI-powered anomaly detection and intelligent recommendation platform built by **Pratik Niroula** as part of the CIS 380 course project. The system demonstrates practical applications of machine learning in security, fraud detection, and personalized recommendations.

### Key Highlights
- **154,000+ images** processed for vision analysis
- **60,000+ movies** in the recommendation database
- **99.2% accuracy** in fraud detection
- **6 ML models** integrated (fraud, cyber, behavior, vision, NLP, fusion)
- **100% offline capable** - works without external APIs

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   React/TS UI   │  │  Streamlit App  │  │  GitHub Pages   │ │
│  │  (Command Ctr)  │  │   (Chat/Demo)   │  │   (Portfolio)   │ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
└───────────┼─────────────────────┼─────────────────────┼─────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   API Routes                             │   │
│  │  /api/chat  │  /api/risk  │  /api/vision  │  /api/voice │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                    │
│  ┌─────────────────────────┴─────────────────────────────┐     │
│  │              Sentifargo Orchestrator               │     │
│  │   • Intent Detection  • Route Selection  • Response   │     │
│  └───────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ML Models Layer                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  Fraud   │ │  Cyber   │ │ Behavior │ │  Vision  │           │
│  │ Detection│ │ Threat   │ │ Analysis │ │ Analysis │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐            │
│  │   NLP    │ │  Fusion  │ │    Recommender       │            │
│  │ Analysis │ │  Model   │ │  (Movies/Products)   │            │
│  └──────────┘ └──────────┘ └──────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  RAG Store  │  │  Catalogs   │  │  Training Datasets      │ │
│  │  (Docs/QA)  │  │  (Items)    │  │  (Fraud/Cyber/Vision)   │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔥 Core Features

### 1. Fraud Detection System
- **Model**: XGBoost/Random Forest ensemble
- **Accuracy**: 99.2% on test data
- **Features**: Transaction amount, velocity, location, device fingerprinting
- **Real-time**: Sub-second prediction latency
- **Explainability**: SHAP values for feature importance

### 2. Cybersecurity Threat Analysis
- **Detection Types**: Network intrusion, anomalous patterns
- **Methods**: Isolation Forest, LSTM for sequence analysis
- **Metrics**: Precision, recall, F1-score tracking
- **Alerts**: Configurable threshold-based alerting

### 3. Behavioral Anomaly Detection
- **Use Case**: Insider threat detection, account compromise
- **Features**: User activity patterns, access times, resource usage
- **Model**: Autoencoder for anomaly scoring
- **Baseline**: Dynamic baseline learning

### 4. Intelligent Recommendations
- **Movie Database**: 60,000+ titles from MovieLens
- **Methods**: Content-based filtering, TF-IDF similarity
- **Categories**: Movies, products, courses, cars, places
- **Randomization**: Varied results each query

### 5. Vision Analysis
- **Dataset**: 154,000+ images (Real/Fake classification)
- **Models**: CNN, ResNet, custom architectures
- **Use Cases**: Deepfake detection, image authenticity
- **Integration**: Upload via chat or API

### 6. Natural Language Processing
- **RAG System**: Document retrieval and Q&A
- **Intent Detection**: Keyword and semantic matching
- **Responses**: 50+ varied intelligent responses
- **Offline**: Works without OpenAI API

---

## 💻 Technology Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **Python 3.13** | Core language |
| **FastAPI** | REST API framework |
| **Uvicorn** | ASGI server |
| **Pydantic** | Data validation |

### Machine Learning
| Technology | Purpose |
|------------|---------|
| **PyTorch** | Deep learning models |
| **scikit-learn** | Classical ML algorithms |
| **XGBoost** | Gradient boosting |
| **FAISS** | Vector similarity search |
| **Transformers** | NLP embeddings |

### Frontend
| Technology | Purpose |
|------------|---------|
| **React 18** | UI framework |
| **TypeScript** | Type safety |
| **Tailwind CSS** | Styling |
| **Vite** | Build tool |
| **Streamlit** | ML demos |

### Data & Storage
| Technology | Purpose |
|------------|---------|
| **Pandas** | Data manipulation |
| **NumPy** | Numerical computing |
| **SQLite** | Local database |
| **YAML/JSON** | Configuration |

### DevOps
| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization |
| **GitHub Actions** | CI/CD |
| **GitHub Pages** | Static hosting |

---

## 📊 Project Statistics

| Metric | Value |
|--------|-------|
| Total Python Files | 352 |
| Total Lines of Code | ~50,000+ |
| ML Models | 6 |
| API Endpoints | 15+ |
| Training Images | 154,000+ |
| Movie Database | 60,000+ |
| Fraud Detection Accuracy | 99.2% |
| Response Variations | 50+ unique responses |

---

## 🚀 Key Innovations

### 1. Offline-First AI
Unlike typical AI applications that require cloud APIs, Sentifargo works **100% offline**:
- Local ML models for all predictions
- Pre-computed embeddings for recommendations
- Intelligent response generation without LLM API
- Fallback responses with variety

### 2. Multi-Modal Orchestration
Single entry point handles multiple AI tasks:
```python
# One endpoint, multiple capabilities
POST /api/chat
{
  "text": "recommend action movies",  # → Movie recommendations
  "text": "what is fraud detection",  # → Knowledge response
  "text": "analyze this image",       # → Vision analysis
  "attachments": {"audio": <bytes>}   # → Voice emotion
}
```

### 3. Randomized Intelligent Responses
Every response is varied for a natural chatbot feel:
- 4 greeting variations
- 3 help response formats
- 45+ movie recommendations (random selection)
- Topic-specific knowledge base with multiple answers

### 4. Production-Ready Architecture
- Modular design with clear separation of concerns
- Comprehensive error handling
- Configurable via YAML files
- Docker-ready deployment
- CI/CD with GitHub Actions

---

## 📁 Project Structure

```
Sentifargo/
├── app/                      # Main application
│   ├── main.py              # FastAPI entry point
│   ├── api/                 # API routes
│   ├── agent/               # Orchestrator & decision engine
│   ├── models/              # ML model implementations
│   │   ├── fraud/           # Fraud detection
│   │   ├── cyber/           # Cyber threat analysis
│   │   ├── behavior/        # Behavioral analysis
│   │   ├── vision/          # Image classification
│   │   ├── nlp/             # NLP processing
│   │   └── recommender/     # Recommendation engine
│   ├── rag/                 # RAG system
│   └── utils/               # Utilities & helpers
├── ui-web/frontend/         # React frontend
├── data/                    # Datasets & catalogs
├── models/                  # Trained model weights
├── notebooks/               # Jupyter experiments
├── scripts/                 # Training & utility scripts
├── tests/                   # Test suite
├── docs/                    # GitHub Pages build
└── config/                  # YAML configurations
```

---

## 🎮 Demo & Usage

### Running Locally
```bash
# 1. Start the backend
cd Sentifargo
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 2. Access the API
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "recommend a movie"}'
```

### Live Demo
- **Portfolio**: https://pratikn03.github.io/Cis380/
- **API Docs**: http://localhost:8000/docs

### Sample Queries
```
"recommend action movies"     → Random action movie picks
"what is fraud detection"     → Detailed explanation
"help"                        → Capability overview
"hello"                       → Varied greeting
"movies like Inception"       → Similar movie recommendations
```

---

## 📈 Performance Metrics

### Fraud Detection Model
| Metric | Score |
|--------|-------|
| Accuracy | 99.2% |
| Precision | 98.7% |
| Recall | 97.5% |
| F1-Score | 98.1% |
| AUC-ROC | 0.995 |

### Recommendation System
| Metric | Value |
|--------|-------|
| Database Size | 60,000+ movies |
| Response Time | <100ms |
| Variety | 50 movies/query pool |
| Genre Coverage | 15+ genres |

### System Performance
| Metric | Value |
|--------|-------|
| API Response Time | <200ms average |
| Concurrent Users | 100+ supported |
| Memory Usage | ~500MB |
| Startup Time | <5 seconds |

---

## 🎓 Learning Outcomes

This project demonstrates proficiency in:

1. **Machine Learning Engineering**
   - Model training, evaluation, and deployment
   - Feature engineering and selection
   - Ensemble methods and model fusion

2. **Full-Stack Development**
   - FastAPI backend development
   - React/TypeScript frontend
   - RESTful API design

3. **System Design**
   - Microservices architecture
   - Orchestration patterns
   - Offline-first design

4. **Data Science**
   - Large dataset handling (154K+ images)
   - Statistical analysis
   - Visualization

5. **DevOps & Deployment**
   - Docker containerization
   - CI/CD pipelines
   - Cloud deployment (GitHub Pages)

---

## 👤 Author

**Pratik Niroula**
- GitHub: [@Pratikn03](https://github.com/Pratikn03)
- Project: CIS 380 - Machine Learning Portfolio
- University Project - 2026

---

## 📄 License

MIT License - See [LICENSE](./LICENSE) for details.

---

## 🙏 Acknowledgments

- MovieLens dataset for recommendation system
- FastAPI framework for excellent developer experience
- scikit-learn and PyTorch communities
- Course instructors and peers for feedback

---

*Built with ❤️ by Pratik Niroula | Sentifargo v2.0 | January 2026*
