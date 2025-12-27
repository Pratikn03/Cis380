# Local Run (Legacy Notes)

This file is retained because older drafts referenced a separate API stack under `deploy/`.

## Recommended Local Run (Current)

- FastAPI: `uvicorn app.main:app --reload`
- Streamlit: `streamlit run app/streamlit_chatbot/app.py`
- Demo walkthrough: `docs/guides/demo.md`

## Legacy Entry Points (Reference Only)
- FastAPI: `uvicorn deploy.api.main:app --reload --port 8000`

The legacy `dashboard/` Streamlit app has been removed; use `app/streamlit_chatbot/app.py` instead.
