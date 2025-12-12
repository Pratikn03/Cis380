# 🧠 **OmniChatX – Unified Multi-Domain AI Agent**

### *OmniNex Chat (UAIS-V) is a universal AI agent platform that routes intent across RAG, recommendations, and risk/anomaly detection so you can surface the right intelligence in one product story.*

---

## 🎯 Elevator pitch

OmniNex Chat is **not just a chatbot**—it is an orchestrator that understands user intent, decides which intelligence (RAG, recommender, or anomaly model) should answer, and delivers structured, explainable outputs plus product-ready UI/metrics. Think of it as **a single agent that offers both positive intelligence (recommendations/RAG) and negative intelligence (fraud/cyber/behavior scoring)** through a consistent backend (FastAPI), ML models, and demo workflow.

## ✍️ Resume + interview-ready brag

*Resume bullet (copy/paste):*  
`OmniNex Chat (UAIS-V) — Multi-Domain AI Agent Platform`  
Built a FastAPI-based agent that routes user intent across RAG document Q&A, personalized MovieLens-style recommendations, and anomaly/risk scoring (fraud, cyber, behavior), with dedicated UI tabs, `/metrics` observability, and structured explanations for explainability tooling.

*Interview-friendly summary:*  
“I built OmniNex Chat to orchestrate recommendations and risk scoring in one system—FastAPI routes the intent, RAG/LLM/ML modules supply answers, and Streamlit or the static UI surfaces results with metrics/demo scripts so the project feels like a real product.”

## 🔌 Extended recommendation domains

OmniNex Chat now understands consumer electronics queries such as “Recommend a phone under $800” or “Best noise-canceling headphones”, plus learning requests such as “Best machine learning course for beginners”. Electronics queries route to CSV-backed handlers that load `data/raw/recommendation/{phones,laptops,headphones}.csv`, filter by price/rating/tags, and return the top-N items. Course requests use `data/raw/recommendation/courses.csv` to match desired skills and difficulties so students can get tailored learning pathways.

## 💸 Budget & Decision Helper

When users include constraints like “budget”, “under $1000”, or a specific use case (“for programming”, “travel”), the electronics recommender synthesizes those filters into a lightweight decision helper: it automatically applies the numeric budget, highlights matched tags, and returns a `tradeoff` note describing the selected price/use case versus rating/popularity. This lets you use OmniNex Chat as a quick decision-support agent without adding new ML models.

## 🧠 Preference memory + trust overlay

OmniNex Chat now keeps light user preferences via `app/chatbot/context_manager.py`: after each recommendation query it stores the last intent, price preference, and favored tags, so subsequent requests can reuse those filters with no external memory service. On top of that, the recommender now runs a mini risk check (powered by the fraud model via `agent/orchestrator.py`) and returns a “Risk overlay” note when a recommendation carries unusual patterns, so you surface trust warnings alongside the standard result cards.

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
* Uses TF-IDF embeddings (scikit-learn pipeline)
* Vector search through custom Vector Store
* Document pipeline (`rag/loader.py`, `rag/embed.py`, `rag/retriever.py`) loads local docs, TF-IDF embeds them, and retrieves nearest passages.
* Drop `.txt`/`.md`/`.pdf` files into `data/docs/` (see `data/docs/README.md`) to refresh the RAG knowledge base.
* Career / job resources live in `data/docs/job_roles.md` and `data/docs/skill_maps.txt` so you can ask “What skills does an ML engineer need?” or “Compare data scientist vs ML engineer” and receive grounded answers.

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
* Risk & Anomaly tab exposes the fraud/cyber/behavior models with a simple feature form
* The Streamlit portal respects `OMNINEX_BACKEND` (defaults to `http://localhost:8000`) for API targets, so set it if your FastAPI app runs elsewhere.

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
/api/vision/train
/metrics
```

`/metrics` exposes Prometheus request/latency statistics for observability; it also powers structured logging via `backend/main.py`.
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
│   │   ├── vision.py
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

## 🎬 **Quick Demo (Five minutes)**

Follow `docs/demo.md` for a scripted walkthrough that covers bootstrapping the backend, the Streamlit UI tabs, fraud/cyber/behavior scoring, RAG answers, the vision/train endpoint, and `/metrics`.

```
docs/demo.md
```

Drop real `.txt/.md/.pdf` content into `data/docs/` before the demo so the RAG answer is populated.

---

## ⚡ **Setup & Installation**

### ► Create environment

```

## 🧪 **Testing**

```
pytest
```

The suite now skips TensorFlow/HuggingFace-heavy code by default (the `tests/test_multi_sequence_30_tf.py` and `tests/test_nlp_tiny.py` helpers only run when the dependency chain works). Set `RUN_TF_TESTS=1` before calling `pytest` if you have a working TensorFlow build and want those tests to execute; the same flag also controls whether `set_global_seed` initializes TensorFlow randomness.
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

## 🏃‍♂️ Quickstart (FastAPI + Static UI)

1) Start backend (from repo root):
```bash
source venv/bin/activate
bash scripts/start_all.sh   # uvicorn backend.main:app
```

2) Open UI:
```
http://localhost:8000/ui/
```

3) APIs:
- `GET /health` (ping)
- `POST /api/chat` (main chat, routed by orchestrator)
- `POST /api/rag/query` (doc search)
- `POST /api/fraud`, `/api/cyber`, `/api/behavior`, `/api/recommend`

### Training entrypoints
- Recommender: `python src/train/train_recommender.py`
- Fusion meta-model: `python src/train/train_fusion.py`
- MovieLens recommender: `python src/train/train_movielens_recommender.py` (expects `data/raw/recommendation/movielens.csv` with userId,movieId,rating)
- Hybrid recsys (tabular): `python recommender/models/train_xgboost.py`
- Hybrid recsys (LightFM, optional): `python recommender/models/train_lightfm.py` (requires `pip install -r requirements-optional.txt`)
- Hybrid recsys (NCF, optional, PyTorch): `python recommender/models/train_ncf.py`

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
