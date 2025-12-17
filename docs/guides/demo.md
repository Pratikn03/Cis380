# OmniNex Chat / OmniChatX Demo Script

Run this script when you want to show OmniNex Chat in under five minutes (perfect for recruiters, teammates, or interviews).

## 1. Start the backend

```bash
source .venv-macos/bin/activate
pip install -r requirements.txt
pip install -e .
uvicorn app.main:app --reload
```

Leave this running; it serves (highlights):

* `/api/chat` + `/api/chat/multimodal`
* `/api/recommend` + `/api/recommend/multimodal`
* `/api/fraud`, `/api/cyber`, `/api/behavior`
* `/api/risk/analyze`
* `/api/monitor/summary` + `/api/monitor/drift`
* `/metrics`
* the optional `/ui/` static site under `/ui/index.html`

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

The UI respects `OMNICHATX_BACKEND` if your FastAPI server runs somewhere other than `http://localhost:8000`.

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
* Change `OMNICHATX_BACKEND` to the production host before demos that hit deployed APIs.  
