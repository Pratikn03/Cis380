"""UAIS-V Streamlit Command Center.

Top-level layout:
- Recommendations (text + multimodal)
- Live Agent Chat
- Audio/Video/Vision (live + uploads)
- Fraud/Cyber/Behavior (risk + scoring)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
import streamlit as st

# Ensure package import works when launched via streamlit run
THIS_DIR = Path(__file__).resolve().parent
APP_ROOT = THIS_DIR.parent
REPO_ROOT = THIS_DIR.parents[1]

# NOTE: This file is named `app.py`, and Streamlit may load it under the module
# name `app`, which can shadow the repo's `app/` package. To avoid that, we:
# - import from `agent.*`, `rag.*` (repo-root packages) and `chatbot.*`,
#   `streamlit_chatbot.*` (packages under app/)
# - ensure REPO_ROOT is searched before APP_ROOT
desired_sys_path = [str(REPO_ROOT), str(APP_ROOT)]
for p in desired_sys_path:
    while p in sys.path:
        sys.path.remove(p)
sys.path.insert(0, desired_sys_path[0])
sys.path.insert(1, desired_sys_path[1])

from streamlit_chatbot.ui.theme import apply_partik_theme, sidebar_panel  # noqa: E402
from streamlit_chatbot.pages.command_center import render_command_center  # noqa: E402
from streamlit_chatbot.pages.live import render_live_page  # noqa: E402
from streamlit_chatbot.pages.brand import render_brand_page  # noqa: E402
from streamlit_chatbot.pages.tools import render_tools_page  # noqa: E402
from streamlit_chatbot.pages.voice_chat import render_voice_chat_page  # noqa: E402
from streamlit_chatbot.risk_dashboard import render_risk_command_center  # noqa: E402
from streamlit_chatbot.chatgpt_style import render_chatgpt_style  # noqa: E402


def main():
    # Backward-compatible backend URL env var.
    # README uses OMNICHATX_BACKEND; older docs used OMNINEX_BACKEND.
    backend_url = (
        (os.environ.get("OMNICHATX_BACKEND") or os.environ.get("OMNINEX_BACKEND") or "http://localhost:8000")
        .strip()
        .rstrip("/")
    )

    apply_partik_theme()
    backend_url = sidebar_panel(backend_url=backend_url)

    def _auth_headers() -> dict[str, str]:
        headers: dict[str, str] = {}
        if os.getenv("AUTH_TOKEN"):
            headers["Authorization"] = f"Bearer {os.environ['AUTH_TOKEN']}"
        return headers

    def call_model(path: str, payload: dict) -> dict:
        try:
            resp = requests.post(
                f"{backend_url}{path}",
                json=payload,
                headers=_auth_headers(),
                timeout=15.0,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            return {"error": f"{exc}"}

    def call_get(path: str, *, params: dict[str, object] | None = None, timeout: float = 15.0) -> dict:
        try:
            resp = requests.get(
                f"{backend_url}{path}",
                params=params,
                headers=_auth_headers(),
                timeout=timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            return {"error": f"{exc}"}

    def call_multipart(
        path: str,
        *,
        data: dict[str, str],
        files: dict[str, tuple[str, bytes, str]] | None,
        timeout: float = 90.0,
    ) -> dict:
        try:
            resp = requests.post(
                f"{backend_url}{path}",
                data=data,
                files=files,
                headers=_auth_headers(),
                timeout=timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            return {"error": f"{exc}"}

    def call_upload(path: str, *, filename: str, content: bytes, content_type: str) -> dict:
        files = {"file": (filename, content, content_type)}
        return call_multipart(path, data={}, files=files, timeout=60.0)

    top_tabs = st.tabs(
        [
            "💬 ChatGPT Style",
            "Recommendations",
            "Live Agent",
            "Audio/Video/Vision",
            "Fraud/Cyber/Behavior",
        ]
    )

    with top_tabs[0]:
        render_chatgpt_style(
            backend_url=backend_url,
            call_model=call_model,
            call_multipart=call_multipart,
            auth_headers=_auth_headers,
        )

    with top_tabs[1]:
        render_command_center(backend_url=backend_url, call_model=call_model, call_multipart=call_multipart)

    with top_tabs[2]:
        st.markdown("## Live Agent Chat")
        st.caption("Calls `/api/chat` (and `/api/chat/multimodal` when you attach media).")

        if "agent_chat_messages" not in st.session_state:
            st.session_state.agent_chat_messages = []

        attach_cols = st.columns(3)
        with attach_cols[0]:
            agent_audio = st.file_uploader(
                "Attach audio (optional)",
                type=["wav", "mp3", "m4a", "aac", "ogg"],
                key="agent_chat_audio",
            )
        with attach_cols[1]:
            agent_image = st.file_uploader(
                "Attach image (optional)",
                type=["png", "jpg", "jpeg", "webp"],
                key="agent_chat_image",
            )
        with attach_cols[2]:
            agent_video = st.file_uploader(
                "Attach video (optional)",
                type=["mp4", "mov", "avi", "mkv"],
                key="agent_chat_video",
            )

        use_rag = st.checkbox("Use RAG", value=True, key="agent_chat_use_rag")
        transcribe_audio = st.checkbox("Transcribe audio (STT)", value=False, key="agent_chat_stt")
        stt_language = st.text_input("STT language (optional, e.g. en)", value="", key="agent_chat_stt_lang")
        user_id = st.text_input("User id", value="streamlit", key="agent_chat_user_id")

        for msg in st.session_state.agent_chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        prompt = st.chat_input("Ask the agent…", key="agent_chat_input")
        if prompt:
            user_text = prompt.strip()
            if not user_text:
                st.info("Type a message to send.")
                user_text = ""

            if user_text:
                st.session_state.agent_chat_messages.append({"role": "user", "content": user_text})
                with st.chat_message("user"):
                    st.markdown(user_text)

                with st.chat_message("assistant"):
                    with st.spinner("Thinking…"):
                        files: dict[str, tuple[str, bytes, str]] = {}
                        if agent_audio is not None:
                            files["audio"] = (
                                agent_audio.name or "audio.wav",
                                agent_audio.getvalue(),
                                agent_audio.type or "audio/wav",
                            )
                        if agent_image is not None:
                            files["image"] = (
                                agent_image.name or "image.jpg",
                                agent_image.getvalue(),
                                agent_image.type or "image/jpeg",
                            )
                        if agent_video is not None:
                            files["video"] = (
                                agent_video.name or "video.mp4",
                                agent_video.getvalue(),
                                agent_video.type or "video/mp4",
                            )

                        if files:
                            res = call_multipart(
                                "/api/chat/multimodal",
                                data={
                                    "message": user_text,
                                    "user_id": user_id,
                                    "use_rag": "true" if use_rag else "false",
                                    "transcribe_audio": "true" if transcribe_audio else "false",
                                    "stt_language": (stt_language or "").strip(),
                                },
                                files=files,
                                timeout=120.0,
                            )
                        else:
                            res = call_model(
                                "/api/chat", {"message": user_text, "user_id": user_id, "use_rag": use_rag}
                            )

                        if not isinstance(res, dict) or "error" in res:
                            reply = (res or {}).get("error") if isinstance(res, dict) else str(res)
                            st.error(reply)
                            st.session_state.agent_chat_messages.append({"role": "assistant", "content": reply})
                        else:
                            reply = res.get("reply") or res.get("answer") or "OK"
                            st.markdown(reply)
                            with st.expander("Meta", expanded=False):
                                st.json(res)
                            st.session_state.agent_chat_messages.append({"role": "assistant", "content": reply})

    with top_tabs[3]:
        media_tabs = st.tabs(["Live (Mic/Webcam)", "Voice Chat", "Uploads", "Brand Recognition"])
        with media_tabs[0]:
            render_live_page(backend_url=backend_url, call_multipart=call_multipart, auth_headers=_auth_headers)
        with media_tabs[1]:
            render_voice_chat_page(
                backend_url=backend_url,
                call_model=call_model,
                call_multipart=call_multipart,
                auth_headers=_auth_headers,
            )
        with media_tabs[2]:
            render_tools_page(call_upload=call_upload)
        with media_tabs[3]:
            render_brand_page(call_upload=call_upload)

    with top_tabs[4]:
        risk_tabs = st.tabs(["Risk Command Center", "Direct Model Scoring", "Monitoring & Logs"])
        with risk_tabs[0]:
            render_risk_command_center(backend_url=backend_url, auth_headers=_auth_headers)
        with risk_tabs[1]:
            st.markdown("## Direct Model Scoring")
            st.caption("Send numeric features to `/api/fraud`, `/api/cyber`, or `/api/behavior`.")

            def render_form(title: str, endpoint: str, key: str) -> None:
                st.subheader(title)
                features_input = st.text_area(
                    f"Features (comma-separated numbers for {title.lower()})",
                    value="0, 0, 0, 0, 0, 0, 0, 0",
                    key=f"{key}_features",
                    height=80,
                )
                if not st.button(f"Score {title}", key=f"{key}_submit"):
                    return
                try:
                    values = [float(x.strip()) for x in features_input.split(",") if x.strip()]
                except ValueError:
                    st.error("Please provide only numbers, separated by commas.")
                    return
                result = call_model(endpoint, {"features": values})
                if isinstance(result, dict) and "error" in result:
                    st.error(result["error"])
                else:
                    st.json(result)

            render_form("Fraud", "/api/fraud", "fraud")
            render_form("Cyber", "/api/cyber", "cyber")
            render_form("Behavior", "/api/behavior", "behavior")

        with risk_tabs[2]:
            st.markdown("## Monitoring & Logs")
            st.caption("Reads from `data/monitoring/logs` via `/api/monitor/*` endpoints.")

            window_n = st.slider("Window size (events)", min_value=10, max_value=5000, value=250, step=10)
            refresh = st.button("Refresh metrics", key="monitor_refresh", type="secondary")

            if refresh or "monitor_summary" not in st.session_state:
                st.session_state.monitor_summary = call_get("/api/monitor/summary", params={"window_n": window_n})

            summary = st.session_state.get("monitor_summary") or {}
            if isinstance(summary, dict) and "error" in summary:
                st.error(summary["error"])
            else:
                paths = (summary or {}).get("paths") if isinstance(summary, dict) else None
                if isinstance(paths, dict):
                    st.caption(f"Fraud log: `{paths.get('fraud_log')}` • Risk log: `{paths.get('risk_log')}`")

                # Fraud metrics (top-level keys for backward compatibility)
                c1, c2, c3 = st.columns(3)
                c1.metric("Fraud events", str((summary or {}).get("count", 0)))
                c2.metric("Avg fraud score", f"{float((summary or {}).get('avg_score', 0.0)):.3f}")
                c3.metric("Avg fraud latency (ms)", f"{float((summary or {}).get('avg_latency', 0.0)):.1f}")

                risk = (summary or {}).get("risk") if isinstance(summary, dict) else None
                if isinstance(risk, dict):
                    st.divider()
                    st.subheader("Risk summary")
                    rc1, rc2, rc3, rc4 = st.columns(4)
                    rc1.metric("Risk events", str(risk.get("total_events", 0)))
                    avg = risk.get("avg_risks") or {}
                    rc2.metric("Avg cyber", f"{float(avg.get('cyber_risk', 0.0)):.3f}")
                    rc3.metric("Avg behavior", f"{float(avg.get('behavior_risk', 0.0)):.3f}")
                    rc4.metric("Avg fraud", f"{float(avg.get('fraud_risk', 0.0)):.3f}")
                    with st.expander("Decision counts", expanded=False):
                        st.json(risk.get("decision_counts") or {})

            st.divider()
            st.subheader("Recent events (tail)")
            kind = st.selectbox("Log kind", ["risk", "fraud"], index=0, key="monitor_kind")
            tail_n = st.slider("Tail N", min_value=5, max_value=500, value=50, step=5, key="monitor_tail_n")
            events_res = call_get("/api/monitor/events", params={"kind": kind, "window_n": tail_n}, timeout=30.0)
            if isinstance(events_res, dict) and "error" in events_res:
                st.error(events_res["error"])
            else:
                events = (events_res or {}).get("events") if isinstance(events_res, dict) else None
                if not events:
                    st.info("No events found yet. Use the Risk Command Center or log fraud events to generate data.")
                else:
                    st.json(events)

    return


if __name__ == "__main__":
    main()
