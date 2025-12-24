# Local Run (Legacy Notes)

This file is retained because older drafts referenced a separate API/UI stack under `deploy/` and `dashboard/`.

## Recommended Local Run (Current)

- FastAPI: `uvicorn app.main:app --reload`
- Streamlit: `streamlit run app/streamlit_chatbot/app.py`
- Demo walkthrough: `docs/guides/demo.md`

## Legacy Entry Points (Reference Only)
- FastAPI: `uvicorn deploy.api.main:app --reload --port 8000`
- Streamlit: `streamlit run dashboard/app_streamlit.py`

These legacy entrypoints are not the default for OmniChatX v2.

