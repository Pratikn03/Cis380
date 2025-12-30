# SentinelForge Demo (5 Minutes)

Use this walkthrough when you want to demo SentinelForge quickly (API + UI).

## 1. Start the backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Leave this running; it serves (highlights):

* `/api/chat` + `/api/chat/multimodal` (+ `/api/chat/stream`)
* `/api/recommend` + `/api/recommend/multimodal` (+ `/api/recommend/explain`)
* `/api/fraud`, `/api/cyber`, `/api/behavior`
* `/api/risk/analyze`
* `/api/monitor/summary` + `/api/monitor/drift`
* `/metrics`
* the optional `/ui/` static site (built from `ui-web/frontend/dist`)

## 2. Launch the Streamlit UI

In a second terminal:

```bash
streamlit run app/streamlit_chatbot/app.py
```

The UI has four main tabs (top bar):

1. **Recommendations** – text recommendations + multimodal (image/text) similarity.
2. **Live Agent** – `/api/chat` with optional media attachments via `/api/chat/multimodal`.
3. **Audio/Video/Vision** – mic/webcam snapshot + optional WebRTC loop, plus uploads (voice/image/video), plus brand recognition.
4. **Fraud/Cyber/Behavior** – Risk Command Center simulator, direct scoring, and monitoring/log viewer.

The UI respects `SENTINELFORGE_BACKEND` if your FastAPI server runs somewhere other than `http://localhost:8000`.
If `AUTH_TOKEN` is set, the UI sends it as a bearer token.

## 3. Demo walkthrough

1. **Recommendations**  
   * In **Recommendations**, enter: `Recommend some sci-fi movies`  
   * Then try: `Recommend budget phones under $600` / `Recommend laptops for programming under $1200`.

2. **Multimodal similarity**  
   * In **Recommendations → Multimodal**, upload an image + type: `Find items like this`.

3. **Live agent (multimodal chat)**  
   * In **Live Agent**, attach an image/audio/video and ask: `What do you detect?`  
   * Show that the response includes `meta.attachments` for voice/vision outputs.

4. **Risk simulator + monitoring**  
   * In **Fraud/Cyber/Behavior → Risk Command Center**, click **Analyze Risk** a few times.  
   * Then open **Monitoring & Logs** and show `/api/monitor/summary` plus the tail of `risk_events.jsonl`.

5. **Metrics**  
   * Open `/metrics` to show Prometheus counters/latency.

## 4. Optional polish

* Drop hand-crafted `.txt`/`.md` documents into `data/docs/`, restart uvicorn, and repeat the RAG query to show new knowledge.  
* Change `SENTINELFORGE_BACKEND` to the production host before demos that hit deployed APIs.  
