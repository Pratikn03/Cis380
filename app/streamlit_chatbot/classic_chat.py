"""
Classic Chat UI for SentinelForge
- Chat input at bottom
- Messages displayed top (newest first option)
- Camera and microphone recording
- Modern icons and styling
"""

from __future__ import annotations

import os
from typing import Callable

import requests
import streamlit as st

from .utils import call_with_container_width


def render_classic_chat(
    *,
    backend_url: str,
    call_model: Callable[..., dict],
    call_multipart: Callable[..., dict],
    auth_headers: Callable[[], dict[str, str]],
) -> None:
    """Render a classic chat interface."""

    # Custom CSS for a clean, classic chat layout
    st.markdown(
        """
    <style>
    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Chat container styling */
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding-bottom: 100px;
    }
    
    /* Message styling */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 18px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }
    
    .assistant-message {
        background: #f0f2f6;
        color: #1a1a2e;
        padding: 12px 18px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        max-width: 80%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Icon styling */
    .icon-btn {
        background: transparent;
        border: none;
        font-size: 24px;
        cursor: pointer;
        padding: 8px;
        border-radius: 50%;
        transition: background 0.2s;
    }
    
    .icon-btn:hover {
        background: rgba(0,0,0,0.1);
    }
    
    /* Input area styling */
    .input-area {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 16px;
        border-top: 1px solid #e0e0e0;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
    }
    
    /* Header styling */
    .chat-header {
        text-align: center;
        padding: 20px;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 20px;
    }
    
    .chat-header h1 {
        margin: 0;
        font-size: 28px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Attachment preview */
    .attachment-preview {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 8px;
        margin: 8px 0;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Media buttons row */
    .media-buttons {
        display: flex;
        gap: 8px;
        margin-bottom: 10px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Header
    st.markdown(
        """
    <div class="chat-header">
        <h1>🤖 SentinelForge Assistant</h1>
        <p style="color: #666; margin-top: 8px;">Fraud • Cyber • Voice • Vision • Recommendations</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Initialize session state
    if "classic_messages" not in st.session_state:
        st.session_state.classic_messages = []
    if "captured_image" not in st.session_state:
        st.session_state.captured_image = None
    if "captured_audio" not in st.session_state:
        st.session_state.captured_audio = None

    # Sidebar with quick actions
    with st.sidebar:
        st.markdown("### ⚡ Quick Actions")

        col1, col2 = st.columns(2)
        with col1:
            if call_with_container_width(st.button, "🗑️ Clear Chat", key="classic_clear_chat"):
                st.session_state.classic_messages = []
                st.session_state.captured_image = None
                st.session_state.captured_audio = None
                st.rerun()

        with col2:
            if call_with_container_width(st.button, "📥 Export", key="classic_export_chat"):
                st.download_button(
                    "💾 Download",
                    data=str(st.session_state.classic_messages),
                    file_name="chat_history.txt",
                    mime="text/plain",
                    key="classic_export_download",
                )

        st.divider()
        st.markdown("### 🎯 Capabilities")
        st.markdown(
            """
        - 💳 **Fraud Detection**
        - 🛡️ **Cyber Security**
        - 🎤 **Voice Emotion**
        - 👁️ **Vision Analysis**
        - 🎬 **Video Analysis**
        - 📊 **Recommendations**
        """
        )

        st.divider()
        st.markdown("### ⚙️ Settings")
        use_rag = st.toggle("📚 Use RAG", value=True, key="classic_rag")
        st.toggle("🔊 Auto TTS", value=False, key="classic_tts")

    # Display chat messages (top area)
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    for msg in st.session_state.classic_messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role == "user":
            col1, col2 = st.columns([1, 5])
            with col2:
                st.markdown(
                    f"""
                <div class="user-message">
                    <strong>👤 You</strong><br>{content}
                </div>
                """,
                    unsafe_allow_html=True,
                )

                # Show attachments if any
                if msg.get("has_image"):
                    st.markdown("📷 *Image attached*")
                if msg.get("has_audio"):
                    st.markdown("🎤 *Audio attached*")
        else:
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(
                    f"""
                <div class="assistant-message">
                    <strong>🤖 Assistant</strong><br>{content}
                </div>
                """,
                    unsafe_allow_html=True,
                )

    st.markdown("</div>", unsafe_allow_html=True)

    # Spacer for fixed input area
    st.markdown("<div style='height: 200px;'></div>", unsafe_allow_html=True)

    # Bottom input area
    st.markdown("---")

    # Media capture row
    st.markdown("##### 📎 Attach Media")
    media_cols = st.columns([1, 1, 1, 1])

    with media_cols[0]:
        camera_input = st.camera_input("📷", key="classic_camera", label_visibility="collapsed")
        if camera_input:
            st.session_state.captured_image = camera_input.getvalue()
            st.success("📷 Photo captured!")

    with media_cols[1]:
        audio_input = st.audio_input("🎤", key="classic_mic", label_visibility="collapsed")
        if audio_input:
            st.session_state.captured_audio = audio_input.read()
            st.success("🎤 Audio recorded!")

    with media_cols[2]:
        uploaded_image = st.file_uploader(
            "🖼️",
            type=["png", "jpg", "jpeg", "webp"],
            key="classic_img_upload",
            label_visibility="collapsed",
        )
        if uploaded_image:
            st.session_state.captured_image = uploaded_image.getvalue()
            st.success("🖼️ Image uploaded!")

    with media_cols[3]:
        uploaded_audio = st.file_uploader(
            "🎵",
            type=["wav", "mp3", "m4a"],
            key="classic_audio_upload",
            label_visibility="collapsed",
        )
        if uploaded_audio:
            st.session_state.captured_audio = uploaded_audio.getvalue()
            st.success("🎵 Audio uploaded!")

    # Show attachment previews
    preview_cols = st.columns(2)
    with preview_cols[0]:
        if st.session_state.captured_image:
            st.image(st.session_state.captured_image, width=100, caption="📷 Attached")
            if st.button("❌ Remove Image", key="remove_img"):
                st.session_state.captured_image = None
                st.rerun()

    with preview_cols[1]:
        if st.session_state.captured_audio:
            st.audio(st.session_state.captured_audio)
            if st.button("❌ Remove Audio", key="remove_audio"):
                st.session_state.captured_audio = None
                st.rerun()

    # Chat input
    st.markdown("##### 💬 Message")
    prompt = st.chat_input("Type your message here...", key="classic_input")

    if prompt:
        user_text = prompt.strip()

        # Add user message
        user_msg = {
            "role": "user",
            "content": user_text,
            "has_image": st.session_state.captured_image is not None,
            "has_audio": st.session_state.captured_audio is not None,
        }
        st.session_state.classic_messages.append(user_msg)

        # Prepare API call
        with st.spinner("🤔 Thinking..."):
            files: dict = {}

            if st.session_state.captured_image:
                files["image"] = ("image.jpg", st.session_state.captured_image, "image/jpeg")

            if st.session_state.captured_audio:
                files["audio"] = ("audio.wav", st.session_state.captured_audio, "audio/wav")

            # Call API
            if files:
                res = call_multipart(
                    "/api/chat/multimodal",
                    data={
                        "message": user_text,
                        "user_id": "streamlit",
                        "use_rag": "true" if use_rag else "false",
                        "transcribe_audio": "true",
                    },
                    files=files,
                    timeout=120.0,
                )
            else:
                res = call_model(
                    "/api/chat", {"message": user_text, "user_id": "streamlit", "use_rag": use_rag}
                )

            # Process response
            if isinstance(res, dict) and "error" not in res:
                reply = res.get("reply") or res.get("answer") or "I processed your request."
            else:
                reply = (
                    f"Error: {res.get('error', 'Unknown error')}"
                    if isinstance(res, dict)
                    else str(res)
                )

            # Add assistant message
            st.session_state.classic_messages.append(
                {
                    "role": "assistant",
                    "content": reply,
                }
            )

            # Clear attachments after sending
            st.session_state.captured_image = None
            st.session_state.captured_audio = None

        st.rerun()


def main():
    """Standalone entry point."""
    st.set_page_config(
        page_title="SentinelForge - Classic Chat",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    backend_url = (
        os.environ.get("SENTINELFORGE_BACKEND")
        or os.environ.get("OMNICHATX_BACKEND")
        or os.environ.get("OMNINEX_BACKEND")
        or "http://localhost:8000"
    ).strip().rstrip("/")

    def _auth_headers() -> dict[str, str]:
        headers: dict[str, str] = {}
        if os.getenv("AUTH_TOKEN"):
            headers["Authorization"] = f"Bearer {os.environ['AUTH_TOKEN']}"
        return headers

    def call_model(path: str, payload: dict) -> dict:
        try:
            resp = requests.post(
                f"{backend_url}{path}", json=payload, headers=_auth_headers(), timeout=15.0
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            return {"error": str(exc)}

    def call_multipart(path: str, *, data: dict, files: dict | None, timeout: float = 90.0) -> dict:
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
            return {"error": str(exc)}

    render_classic_chat(
        backend_url=backend_url,
        call_model=call_model,
        call_multipart=call_multipart,
        auth_headers=_auth_headers,
    )


if __name__ == "__main__":
    main()
