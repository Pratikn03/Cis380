# Sentifargo Command Center Web UI

This folder contains the official web UI for the Sentifargo project.
It is intentionally isolated from the backend and Streamlit UI.

Structure:
- ui-web/frontend: React + TypeScript + Tailwind frontend
- ui-web/deploy: deployment notes and configs

Local quickstart:
1) cd ui-web/frontend
2) npm install
3) npm run dev

Backend defaults to http://localhost:8000 via VITE_API_BASE.
Set a different backend in ui-web/frontend/.env if needed.

GitHub Pages:
- See ui-web/deploy/github-pages.md
- Build with VITE_BASE_PATH=/REPO_NAME/

Streamlit fallback (optional):
streamlit run app/streamlit_chatbot/app.py
