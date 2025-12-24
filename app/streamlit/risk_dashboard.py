"""Legacy Streamlit entrypoint for the Risk Command Center.

This repo has a canonical Streamlit UI at `app/streamlit_chatbot/app.py`.
The Risk Command Center lives under:
  "Fraud/Cyber/Behavior" -> "Risk Command Center"

Keep this file so older docs/bookmarks still work:
  streamlit run app/streamlit/risk_dashboard.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

# Ensure imports work when launched via `streamlit run` without an editable install.
THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[2]
SRC_DIR = REPO_ROOT / "src"
for p in (str(REPO_ROOT), str(SRC_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.streamlit_chatbot.risk_dashboard import render_risk_command_center  # noqa: E402


def render_risk_dashboard() -> None:
    st.set_page_config(page_title="Risk Command Center", layout="wide")

    backend_url = (os.getenv("OMNICHATX_BACKEND") or "http://localhost:8000").strip().rstrip("/")
    token = (os.getenv("AUTH_TOKEN") or "").strip()

    def _auth_headers() -> dict[str, str]:
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}

    render_risk_command_center(backend_url=backend_url, auth_headers=_auth_headers)


if __name__ == "__main__":
    render_risk_dashboard()
