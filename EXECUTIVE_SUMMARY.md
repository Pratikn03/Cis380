# SentinelForge - Executive Summary

## One-Liner
**SentinelForge** is an AI-powered anomaly detection platform combining fraud detection, cybersecurity analysis, and intelligent recommendations in a single offline-capable system.

---

## 🎯 What It Does

| Feature | Description |
|---------|-------------|
| **Fraud Detection** | 99.2% accurate ML model detecting suspicious transactions |
| **Cyber Threat Analysis** | Network anomaly detection using Isolation Forest |
| **Smart Recommendations** | 60K+ movies with personalized suggestions |
| **Vision Analysis** | 154K+ images for authenticity detection |
| **Intelligent Chat** | 50+ varied responses without requiring APIs |

---

## 🛠️ Tech Stack

**Backend**: Python 3.13, FastAPI, PyTorch, scikit-learn, XGBoost  
**Frontend**: React 18, TypeScript, Tailwind CSS  
**ML**: Random Forest, Isolation Forest, CNN, TF-IDF  
**Data**: 154K images, 60K movies, 100K transactions  

---

## 💡 Key Innovation

**Offline-First AI** - Unlike typical chatbots requiring OpenAI/cloud APIs:
- All ML models run locally
- 50+ intelligent response variations
- Zero external API dependencies
- Sub-second response times

---

## 📊 By The Numbers

| Metric | Value |
|--------|-------|
| Python Files | 352 |
| Lines of Code | ~50,000 |
| ML Models | 6 |
| Training Images | 154,000+ |
| Movie Database | 60,000+ |
| Fraud Accuracy | 99.2% |

---

## 🚀 Quick Demo

```bash
# Start server
uvicorn app.main:app --port 8000

# Test chat
curl -X POST http://localhost:8000/api/chat \
  -d '{"text": "recommend action movies"}'

# Response: Different movies every time!
```

---

## 📁 Architecture

```
User → FastAPI → Orchestrator → ML Models → Response
                      ↓
         [Fraud | Cyber | Vision | NLP | Recommender]
```

---

## 🎓 Skills Demonstrated

- Machine Learning Engineering
- Full-Stack Development (Python + React)
- API Design & System Architecture
- Data Science (large dataset handling)
- DevOps (Docker, CI/CD, deployment)

---

## 👤 Author

**Pratik Niroula** | CIS 380 Project | 2026

🔗 Live: https://pratikn03.github.io/Cis380/  
📂 GitHub: github.com/Pratikn03/Cis380

---

*SentinelForge v2.0 - AI Security & Recommendations Platform*
