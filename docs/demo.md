# OmniNex Chat / OmniChatX Demo Script

Run this script when you want to show OmniNex Chat in under five minutes (perfect for recruiters, teammates, or interviews).

## 1. Start the backend

```bash
source .venv-macos/bin/activate
pip install -r requirements.txt
pip install -e .
uvicorn backend.main:app --reload
```

Leave this running; it serves:

* `/api/chat`, `/api/rag`, `/api/recommend`, `/api/fraud`, `/api/cyber`, `/api/behavior`
* `/api/vision/train`
* `/metrics`
* the optional `/ui/` static site under `/ui/index.html`

## 2. Launch the Streamlit UI

In a second terminal:

```bash
streamlit run app/streamlit_chatbot/app.py
```

The UI has two tabs:

1. **Chat & Recommendations** – ask for movies, places, or news. It uses `route_recommendation` (or LLM fallback) and renders cards.
2. **Risk & Anomaly** – paste a comma-delimited feature vector (matching the backend model) and click “Score Fraud”, “Score Cyber”, or “Score Behavior” to hit each API.

The UI respects `OMNINEX_BACKEND` if your FastAPI server runs somewhere other than `http://localhost:8000`.

## 3. Demo walkthrough

1. **Movie recommender**  
   * In the Chat tab enter: `Recommend some sci-fi movies`  
   * Demo: `route_recommendation` + curated list with reasons/links.

2. **Fraud detection**  
   * In “Risk & Anomaly”: enter `0,0,0,0,0,0,0,0` (or real features) and click “Score Fraud”.  
   * Show the returned `score`/`probability` plus any SHAP explanation.

3. **Cyber detection**  
   * Reuse the feature input, click “Score Cyber”.  
   * Show threat probability.

4. **Behavior anomaly**  
   * Click “Score Behavior” with the same vector.  
   * Highlight LOF anomaly score in the JSON response.

5. **RAG experiment**  
   * Open `/api/rag/query` (via curl/postman or send a direct `/api/chat` prompt) with `{"query":"Explain the fraud detection pipeline"}` and show the TF-IDF passages from `data/docs/`.

6. **Vision (optional)**  
   * POST to `/api/vision/train` with the default dataset path to showcase the dataset summary and optional training metrics.

7. **Metrics & logs**  
   * Hit `/metrics` in your browser to show Prometheus counters/latency.  
   * Point to the console where uvicorn logs structured request events.

## 4. Optional polish

* Drop hand-crafted `.txt`/`.md` documents into `data/docs/`, restart uvicorn, and repeat the RAG query to show new knowledge.  
* Change `OMNINEX_BACKEND` to the production host before demos that hit deployed APIs.  
