# 🧠 **OmniChatX – Unified Multi-Domain AI Agent**

### *A full-stack AI system integrating LLMs, RAG, multi-domain ML models, anomaly detection, recommendations, and agentic orchestration.*

---

## 🚀 **Overview**

**OmniChatX** is a **Tier-4 AI Agent System** designed to combine:

* 🔥 **LLM Reasoning (OpenAI / Groq / Mistral)**
* 🔍 **RAG (Retrieval-Augmented Generation)**
* 🧩 **Fraud Detection ML Model**
* 🛡 **Cyber Intrusion Detection Model**
* 🧠 **Behavior / Insider Threat Detection**
* 🎯 **Recommendation Engine**
* 🤖 **Agent Orchestrator**
* 🖥 **Streamlit Chatbot + Optional Static UI**

This project demonstrates **end-to-end AI engineering**, including model training, vector search, agent routing, frontend design, API development, and explainability.

It is engineered to serve as a **portfolio-quality AI project** for internships in Machine Learning, AI Engineering, MLOps, and Software Development.

---

## ⭐ **Key Features**

### 🧠 **1. LLM Reasoning**

* ChatGPT-like natural language interface
* Uses OpenAI/Groq/Mistral LLMs
* Default fallback when no specialized model is needed

---

### 📚 **2. RAG (Retrieval-Augmented Generation)**

* Adds factual knowledge from your documents
* Supports PDFs, text files, notes, datasets
* Uses SentenceTransformers embeddings
* Vector search through custom Vector Store

---

### 🔐 **3. Fraud Detection Module**

* Trained on credit card + PaySim datasets
* Predicts fraud probability
* SHAP interpretation support
* API: `/api/fraud`

---

### 🛡 **4. Cyber Intrusion Detection Module**

* Trained on UNSW-NB15 dataset
* Attack classification + risk score
* API: `/api/cyber`

---

### 👤 **5. Behavior / Insider Threat Module**

* Uses CERT r4.2 dataset
* Unsupervised anomaly detection
* API: `/api/behavior`

---

### 🎯 **6. Recommendation Engine**

* Returns intelligent suggestions
* Supports user-item interactions
* API: `/api/recommend`

---

### 🤖 **7. OmniChatX Agent Orchestrator**

A unified agent that decides automatically:

| Task Type                 | Engine Used    |
| ------------------------- | -------------- |
| General questions         | LLM            |
| Document answers          | RAG            |
| Fraud queries             | Fraud ML model |
| Cyber logs                | Cyber model    |
| Employee/insider patterns | Behavior model |
| Recommendation tasks      | Recommender    |
| Other                     | LLM fallback   |

Located in:

```
agent/orchestrator.py
```

---

### 🖥 **8. Frontend UI**

Two options:

#### ✔ **Streamlit UI (active by default)**

Live chatbot interface with:

* session memory
* tool routing
* multi-model support

#### ✔ **Static HTML UI (optional professional layout)**

Located in `/ui` (index.html, styles.css, app.js)

---

### ⚙ **9. FastAPI Backend**

Unified routes:

```
/api/chat
/api/rag
/api/fraud
/api/cyber
/api/behavior
/api/recommend
```

Backend entry point:

```
backend/main.py
```

---

## 🧩 **Project Structure**

```
universal-anomaly-intelligence-v2/
│
├── ui/
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│
├── rag/
│   ├── loader.py
│   ├── embed.py
│   ├── retriever.py
│   ├── vector_store/
│
├── agent/
│   ├── orchestrator.py
│   ├── policy.py
│   ├── utils/
│       ├── shap_explainer.py
│       ├── formatters.py
│
├── backend/
│   ├── api/
│   │   ├── chat.py
│   │   ├── rag.py
│   │   ├── fraud.py
│   │   ├── cyber.py
│   │   ├── behavior.py
│   │   ├── recommend.py
│   ├── main.py
│
├── src/
│   ├── train/
│       ├── train_fraud.py
│       ├── train_cyber.py
│       ├── train_behavior.py
│       ├── train_recommender.py
│
├── data/
│   ├── raw/
│   │   ├── fraud/
│   │   ├── cyber/
│   │   ├── behavior/
│   │   ├── nlp/
│   │   ├── vision/
│   │   ├── recommendation/
│   ├── docs/
│   ├── processed/
│
├── models/
│   ├── fraud_model.pkl
│   ├── cyber_model.pkl
│   ├── behavior_model.pkl
│   ├── recommender_model.pkl
│
├── scripts/
│   ├── start_all.sh
│   ├── rebuild_rag.sh
│
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## ⚡ **Setup & Installation**

### ► Create environment

```
conda create -n omnichatx python=3.10
conda activate omnichatx
pip install -r requirements.txt
```

### ► Start backend (FastAPI)

```
uvicorn backend.main:app --reload
```

### ► Start Streamlit UI

```
streamlit run app/streamlit_chatbot/app.py
```

### ► Optional: Start static UI

Serve `/ui/index.html` using any static server:

```
python3 -m http.server
```

---

## 🔌 API Endpoints

| Endpoint         | Purpose                  |
| ---------------- | ------------------------ |
| `/api/chat`      | LLM conversation         |
| `/api/rag`       | Document retrieval       |
| `/api/fraud`     | Fraud prediction         |
| `/api/cyber`     | Cyber threat detection   |
| `/api/behavior`  | Insider threat detection |
| `/api/recommend` | Recommender system       |

---

## 🧠 **Model Training**

Training scripts are located in:

```
src/train/
```

You can retrain any model:

```
python src/train/train_fraud.py
python src/train/train_cyber.py
python src/train/train_behavior.py
python src/train/train_recommender.py
```

---

## 📘 **How It Works (High-Level)**

1. User sends a message
2. The **Orchestrator** analyzes the intent
3. Based on message type, it chooses:

   * LLM
   * RAG
   * Fraud model
   * Cyber model
   * Behavior model
   * Recommender
4. Engine produces output
5. Orchestrator merges results
6. Streamlit UI displays final response

This creates a **multi-intelligence AI assistant**, not a basic chatbot.

---

## 🏆 **Why This Project Is Special**

* Full end-to-end AI system
* Multiple ML models integrated
* Real agentic reasoning
* Document-aware RAG intelligence
* Modular backend + UI
* Professional architecture
* Internship-level and research-level quality

Companies will see this as equivalent to:

* Junior AI Engineer
* AI Agent Developer
* LLM Integration Engineer
* ML Engineer
* Research Engineer

---

## 👨‍💻 **Future Extensions**

* Add LangGraph for multi-step agents
* Add memory store (Redis / Weaviate)
* Add SLM (Small Language Model) fine-tuned on your domain
* Add logging + monitoring (Prometheus/Grafana)
* Deploy on Render / Railway / HuggingFace Space

---

## 📄 **License**

MIT License

---

## 🙌 **Author**

Created by **You**, as part of a full-stack AI engineering learning project.

---

If you want, I can also create:

### ✔ A polished GitHub banner

### ✔ A one-page internship PDF

### ✔ Resume bullet points

### ✔ System architecture PNG

### ✔ A project pitch paragraph
