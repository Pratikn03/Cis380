"""Streamlit UI primitives (Partik theme).

Keep all shared styling + header UI in one place so pages look consistent.
"""

from __future__ import annotations

import os
from typing import Any

import streamlit as st
import requests


def apply_partik_theme(*, subtitle: str = "Cyber • Fraud • Behavior • Vision • Voice • Recsys") -> None:
    """Apply global CSS theme + render the top header."""

    st.set_page_config(page_title="UAIS-V Command Center", page_icon="🧠", layout="wide")

    st.markdown(
        """
        <style>
        body, .main {
            background: radial-gradient(circle at 10% 10%, rgba(33,55,95,0.45), transparent 35%), 
                        radial-gradient(circle at 80% 20%, rgba(15,23,42,0.7), transparent 45%), 
                        linear-gradient(135deg, #04060c, #05070f 45%, #070a12);
            color: #e5e7eb;
            font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            letter-spacing: 0.01em;
        }
        section.main > div { padding-top: 1.5rem; position: relative; }
        .stApp > header, .stApp > footer { visibility: hidden; }

        .stChatInput > div > div {
            border-radius: 16px !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
            background: rgba(255,255,255,0.03) !important;
            color: #e5e7eb !important;
        }
        .glass-card {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(22px);
            border-radius: 24px;
            padding: 20px 26px;
            box-shadow: 0 20px 45px rgba(2,6,19,0.65);
        }
        .card-panel {
            background: rgba(15,23,42,0.6);
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 15px 30px rgba(1,8,25,0.55);
            border-radius: 24px;
            padding: 24px;
        }
        .metric-card {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 16px 18px;
        }
        .glass-button {
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,0.2);
            background: rgba(255,255,255,0.04);
            color: #f8fafc;
        }
        .muted { color: #94a3b8; }
        .pill {
            display:inline-flex;
            gap:8px;
            align-items:center;
            padding: 6px 12px;
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,0.18);
            background: rgba(255,255,255,0.03);
            font-size: 12px;
            color: #cbd5e1;
            margin-right: 8px;
        }
        .tag {
            display: inline-block;
            padding: 4px 12px;
            margin: 0 6px 6px 0;
            border-radius: 999px;
            background: rgba(255,255,255,0.08);
            color: #c7d2fe;
            font-size: 12px;
            border: 1px solid rgba(255,255,255,0.12);
        }
        .chat-bubble {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 22px;
            padding: 16px 18px;
            box-shadow: 0 10px 30px rgba(1,6,18,0.6);
            margin-bottom: 12px;
            line-height: 1.6;
        }
        .chat-bubble.assistant {
            background: rgba(59,130,246,0.12);
            border-color: rgba(59,130,246,0.4);
        }
        .chat-bubble.user {
            background: rgba(249,115,22,0.2);
            border-color: rgba(249,115,22,0.3);
            align-self: flex-end;
        }
        .chat-row {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .typing-indicator {
            display: flex;
            gap: 4px;
            align-items: center;
        }
        .typing-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: rgba(248,250,252,0.7);
            animation: pulse 1s infinite ease-in-out;
        }
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.6; }
            50% { transform: scale(1.3); opacity: 1; }
        }
        h1, h2, h3, h4, h5, h6 { letter-spacing: 0.04em; color: #f1f5f9; }
        .watermark {
            position: fixed;
            bottom: 26px;
            right: 28px;
            z-index: 0;
            pointer-events: none;
            font-size: 110px;
            color: rgba(255,255,255,0.03);
            font-weight: 700;
            letter-spacing: 4px;
        }
        .footer-note {
            text-align: center;
            font-size: 12px;
            color: rgba(229,231,235,0.6);
            padding: 6px 0;
        }
        @keyframes gradientDrift {
            0%   { background-position: 0% 50%; }
            50%  { background-position: 100% 40%; }
            100% { background-position: 0% 50%; }
        }
        body::before {
            content: "";
            position: fixed;
            inset: 0;
            background: radial-gradient(circle at 20% 20%, rgba(255,255,255,0.04), transparent 40%),
                        radial-gradient(circle at 80% 10%, rgba(255,255,255,0.02), transparent 45%),
                        radial-gradient(circle at 60% 80%, rgba(59,130,246,0.06), transparent 50%),
                        linear-gradient(135deg, rgba(3,5,12,0.8), rgba(5,7,15,0.95));
            animation: gradientDrift 40s ease-in-out infinite;
            z-index: -1;
            opacity: 0.9;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="watermark">OmniChatX</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="glass-card" style="padding:18px 22px;margin-bottom:14px;">
            <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;">
                <div style="display:flex;align-items:center;gap:12px;">
                    <div style="font-size:30px;">🧠</div>
                    <div>
                        <div style="font-size:26px;font-weight:600;letter-spacing:0.04em;">OmniChatX</div>
                        <div class="muted" style="font-size:13px;">Universal AI Intelligence</div>
                    </div>
                </div>
                <div style="display:flex;gap:6px;flex-direction:column;align-items:flex-end;">
                    <span class="pill">Built by Partik</span>
                    <span class="pill">Dec 2025</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="footer-note">Built with local-first AI · OmniChatX</div>',
        unsafe_allow_html=True,
    )


def sidebar_panel(*, backend_url: str) -> str:
    """Sidebar settings + tips (no page navigation)."""

    st.sidebar.markdown("## Settings")
    backend_url = (st.sidebar.text_input("Backend URL", value=backend_url, key="backend_url") or backend_url).strip()
    backend_url = backend_url.rstrip("/")

    st.sidebar.caption(f"AUTH_TOKEN: {'set' if os.getenv('AUTH_TOKEN') else 'not set'}")

    # ---- Backend health + optional features ----
    # Keep this lightweight and non-fatal: if the backend is down or auth blocks
    # the health endpoint, we just show an offline banner.
    try:
        headers: dict[str, str] = {}
        if os.getenv("AUTH_TOKEN"):
            headers["Authorization"] = f"Bearer {os.environ['AUTH_TOKEN']}"

        r = requests.get(f"{backend_url}/api/health", headers=headers, timeout=3.5)
        if r.status_code == 200:
            health: dict[str, Any] = r.json() if isinstance(r.json(), dict) else {}
            raw_feats = health.get("optional_features")
            feats: dict[str, Any] = raw_feats if isinstance(raw_feats, dict) else {}

            st.sidebar.markdown("## Status")
            st.sidebar.success("Backend reachable ✅")
            with st.sidebar.expander("Optional features", expanded=True):
                def _flag(name: str, ok: bool | None) -> str:
                    if ok is True:
                        return f"{name}: ✅"
                    if ok is False:
                        return f"{name}: ⚠️"
                    return f"{name}: —"

                st.write(_flag("WebRTC (mic/webcam)", bool(feats.get("webrtc"))))
                st.write(_flag("STT (speech-to-text)", bool(feats.get("stt"))))
                st.write(_flag("CLIP embeddings", bool(feats.get("clip"))))
                st.write(_flag("FAISS index", bool(feats.get("faiss"))))
        else:
            st.sidebar.markdown("## Status")
            st.sidebar.warning(f"Backend unreachable or blocked (HTTP {r.status_code})")
    except Exception:
        st.sidebar.markdown("## Status")
        st.sidebar.error("Backend unreachable ❌")

    with st.sidebar.expander("Quick tips", expanded=True):
        st.markdown(
            """
            - **Recommendations**: movies/electronics/news + image/text similarity.
            - **Live Agent**: GPT-like chat (uses `OPENAI_API_KEY` if set).
            - **Voice Chat**: upload speech, transcribe via STT, and ask OmniChatX hands-free.
            - **Audio/Video/Vision**: mic/webcam + uploads (voice + image + video).
            - **Fraud/Cyber/Behavior**: risk command center + direct scoring.
            """
        )
        st.caption(f"Backend: {backend_url or 'N/A'}")

    return backend_url
