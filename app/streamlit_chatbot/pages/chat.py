from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
import json
import uuid

import streamlit as st

from streamlit_chatbot.utils import call_with_container_width


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _new_chat_id() -> str:
    return str(uuid.uuid4())


def _ensure_chat_state() -> None:
    if "ocx_chat_sessions" not in st.session_state:
        chat_id = _new_chat_id()
        st.session_state.ocx_chat_sessions = {
            chat_id: {
                "title": "New chat",
                "created_at": _utc_now_iso(),
                "messages": [],
            }
        }
        st.session_state.ocx_chat_active_id = chat_id

    if "ocx_chat_active_id" not in st.session_state:
        st.session_state.ocx_chat_active_id = next(iter(st.session_state.ocx_chat_sessions))

    if "ocx_chat_attach_image" not in st.session_state:
        st.session_state.ocx_chat_attach_image = None
    if "ocx_chat_attach_audio" not in st.session_state:
        st.session_state.ocx_chat_attach_audio = None


def _new_chat() -> None:
    chat_id = _new_chat_id()
    st.session_state.ocx_chat_sessions[chat_id] = {
        "title": "New chat",
        "created_at": _utc_now_iso(),
        "messages": [],
    }
    st.session_state.ocx_chat_active_id = chat_id
    st.session_state.ocx_chat_attach_image = None
    st.session_state.ocx_chat_attach_audio = None


def _delete_chat(chat_id: str) -> None:
    sessions: dict[str, dict] = st.session_state.ocx_chat_sessions
    if chat_id not in sessions:
        return
    del sessions[chat_id]
    if not sessions:
        _new_chat()
        return
    if st.session_state.ocx_chat_active_id == chat_id:
        st.session_state.ocx_chat_active_id = next(iter(sessions))


def _chat_label(chat_id: str, chat: dict) -> str:
    title = str(chat.get("title") or "").strip() or "Untitled"
    return f"{title} · {chat_id[:8]}"


def _set_title_from_first_user_message(chat: dict) -> None:
    messages = chat.get("messages") or []
    for msg in messages:
        if msg.get("role") != "user":
            continue
        text = str(msg.get("content") or "").strip()
        if not text:
            continue
        title = text.splitlines()[0].strip()
        title = title[:42] + ("…" if len(title) > 42 else "")
        chat["title"] = title or "New chat"
        return


def render_chat_page(
    *,
    call_model: Callable[[str, dict], dict],
    call_multipart: Callable[..., dict],
    auth_headers: Callable[[], dict[str, str]],
) -> None:
    """ChatGPT×Gemini-inspired chat UI (session-based)."""

    _ensure_chat_state()

    # ---- Sidebar: sessions ----
    with st.sidebar:
        st.markdown("## Chats")
        if call_with_container_width(st.button, "＋ New chat", key="ocx_new_chat"):
            _new_chat()
            st.rerun()

        sessions: dict[str, dict] = st.session_state.ocx_chat_sessions
        active_id: str = st.session_state.ocx_chat_active_id
        # Newest first
        for chat_id, chat in sorted(
            sessions.items(),
            key=lambda kv: str(kv[1].get("created_at") or ""),
            reverse=True,
        ):
            is_active = chat_id == active_id
            label = ("▶ " if is_active else "") + _chat_label(chat_id, chat)
            if call_with_container_width(st.button, label, key=f"ocx_select_{chat_id}"):
                st.session_state.ocx_chat_active_id = chat_id
                st.session_state.ocx_chat_attach_image = None
                st.session_state.ocx_chat_attach_audio = None
                st.rerun()

        st.divider()
        if call_with_container_width(st.button, "🗑️ Delete current chat", key="ocx_delete_chat"):
            _delete_chat(active_id)
            st.rerun()

    active_id = st.session_state.ocx_chat_active_id
    active_chat: dict = st.session_state.ocx_chat_sessions[active_id]
    messages: list[dict] = active_chat.get("messages") or []

    # ---- Header ----
    st.markdown("## ✨ OmniChatX Chat")
    st.caption("ChatGPT-like sessions with Gemini-style quick prompts. Runs fully local via FastAPI.")

    # ---- Right rail (controls + attachments) ----
    chat_col, rail_col = st.columns([3, 1])
    with rail_col:
        st.markdown("### Controls")
        user_id = (st.text_input("User id", value="streamlit", key="ocx_user_id") or "streamlit").strip()
        use_rag = st.toggle("Use RAG", value=True, key="ocx_use_rag")
        transcribe_audio = st.toggle("Transcribe audio (STT)", value=False, key="ocx_transcribe_audio")
        stt_language = st.text_input("STT language (optional)", value="", key="ocx_stt_language").strip()
        show_meta = st.toggle("Show response details", value=False, key="ocx_show_meta")

        st.divider()
        st.markdown("### Attach")
        attach_tab = st.tabs(["Image", "Audio"])
        with attach_tab[0]:
            cam = st.camera_input("Camera", key="ocx_camera", label_visibility="collapsed")
            up_img = st.file_uploader(
                "Upload image",
                type=["png", "jpg", "jpeg", "webp"],
                key="ocx_img_upload",
                label_visibility="collapsed",
            )
            if cam is not None:
                st.session_state.ocx_chat_attach_image = cam.getvalue()
            if up_img is not None:
                st.session_state.ocx_chat_attach_image = up_img.getvalue()
            if st.session_state.ocx_chat_attach_image:
                st.image(st.session_state.ocx_chat_attach_image, caption="Attached image", width=260)
                if st.button("Remove image", key="ocx_remove_image"):
                    st.session_state.ocx_chat_attach_image = None
                    st.rerun()

        with attach_tab[1]:
            mic = st.audio_input("Mic", key="ocx_mic", label_visibility="collapsed")
            up_audio = st.file_uploader(
                "Upload audio",
                type=["wav", "mp3", "m4a", "aac", "ogg"],
                key="ocx_audio_upload",
                label_visibility="collapsed",
            )
            if mic is not None:
                st.session_state.ocx_chat_attach_audio = mic.read()
            if up_audio is not None:
                st.session_state.ocx_chat_attach_audio = up_audio.getvalue()
            if st.session_state.ocx_chat_attach_audio:
                st.audio(st.session_state.ocx_chat_attach_audio)
                if st.button("Remove audio", key="ocx_remove_audio"):
                    st.session_state.ocx_chat_attach_audio = None
                    st.rerun()

        st.divider()
        export_payload = json.dumps(
            {"chat_id": active_id, "title": active_chat.get("title"), "messages": messages},
            ensure_ascii=False,
            indent=2,
        )
        st.download_button(
            "⬇️ Export chat (JSON)",
            data=export_payload,
            file_name=f"omnichatx_{active_id[:8]}.json",
            mime="application/json",
            key="ocx_export_chat",
        )

    # ---- Chat area ----
    with chat_col:
        if not messages:
            st.markdown("### Try a prompt")
            suggestions = [
                "Summarize the latest fraud + cyber risks in plain English.",
                "I have a suspicious login from a new device—what should I check first?",
                "Recommend 5 movies like Interstellar with a short reason each.",
                "Analyze this image for anomalies and describe what you see.",
            ]
            chips = st.columns(2)
            selected: str | None = None
            for idx, suggestion in enumerate(suggestions):
                with chips[idx % 2]:
                    if call_with_container_width(
                        st.button, suggestion, key=f"ocx_suggestion_{idx}", stretch=True
                    ):
                        selected = suggestion
            if selected:
                messages.append({"role": "user", "content": selected})

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            with st.chat_message(role):
                st.markdown(content)
                meta = msg.get("meta")
                if show_meta and role == "assistant" and isinstance(meta, dict):
                    with st.expander("Details", expanded=False):
                        st.json(meta)

        prompt = st.chat_input("Message OmniChatX…", key="ocx_chat_input")
        if not prompt:
            return

        user_text = prompt.strip()
        if not user_text:
            st.info("Type a message to send.")
            return

        messages.append({"role": "user", "content": user_text})

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                files: dict[str, tuple[str, bytes, str]] = {}
                if st.session_state.ocx_chat_attach_image:
                    files["image"] = ("image.jpg", st.session_state.ocx_chat_attach_image, "image/jpeg")
                if st.session_state.ocx_chat_attach_audio:
                    files["audio"] = ("audio.wav", st.session_state.ocx_chat_attach_audio, "audio/wav")

                if files:
                    res = call_multipart(
                        "/api/chat/multimodal",
                        data={
                            "message": user_text,
                            "user_id": user_id,
                            "use_rag": "true" if use_rag else "false",
                            "transcribe_audio": "true" if transcribe_audio else "false",
                            "stt_language": stt_language,
                        },
                        files=files,
                        timeout=120.0,
                    )
                else:
                    res = call_model(
                        "/api/chat",
                        {"message": user_text, "user_id": user_id, "use_rag": use_rag},
                    )

                if isinstance(res, dict) and "error" not in res:
                    reply = res.get("reply") or res.get("answer") or "OK"
                else:
                    reply = (res or {}).get("error") if isinstance(res, dict) else str(res)
                    reply = f"Error: {reply}"

                st.markdown(reply)
                messages.append({"role": "assistant", "content": reply, "meta": res})

                st.session_state.ocx_chat_attach_image = None
                st.session_state.ocx_chat_attach_audio = None
                _set_title_from_first_user_message(active_chat)

        st.rerun()
