from __future__ import annotations

from typing import Callable

import requests
import streamlit as st


def _tts_playback(
    backend_url: str, text: str, auth_headers: Callable[[], dict[str, str]]
) -> bytes | None:
    try:
        resp = requests.post(
            f"{backend_url}/api/tts/speak",
            json={"text": text},
            headers=auth_headers(),
            timeout=60.0,
        )
        resp.raise_for_status()
        return resp.content
    except Exception as exc:
        st.error(f"TTS request failed: {exc}")
        return None


def render_voice_chat_page(
    *,
    backend_url: str,
    call_model: Callable[..., dict],
    call_multipart: Callable[..., dict],
    auth_headers: Callable[[], dict[str, str]],
) -> None:
    st.markdown("## Voice Chat (STT → /api/chat)")
    st.caption("Upload audio, transcribe via STT, and send the transcript to SentinelForge.")

    st.markdown(
        """
        <div class="glass-card">
            <p class="muted">
                Use any speech (wav/mp3/m4a). We stream the audio to `/api/stt/transcribe`,
                display the transcript, and let you ask SentinelForge without typing.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    audio_file = st.file_uploader(
        "Upload speech recording",
        type=["wav", "mp3", "m4a", "ogg", "flac"],
        key="voice_chat_upload",
    )

    stt_language = st.text_input("STT language (optional)", value="", key="voice_chat_language")

    if audio_file:
        st.audio(audio_file)
        if st.button("Transcribe audio", key="voice_transcribe"):
            payload = {
                "language": (stt_language or "").strip(),
            }
            files = {
                "file": (
                    audio_file.name or "voice.wav",
                    audio_file.getvalue(),
                    audio_file.type or "audio/wav",
                )
            }
            res = call_multipart(
                "/api/stt/transcribe",
                data={k: v for k, v in payload.items() if v},
                files=files,
                timeout=120.0,
            )
            if "error" in res:
                st.error(res["error"])
            else:
                st.session_state.voice_transcript = res.get("text", "")
                st.session_state.voice_segments = res.get("segments", [])

    transcript = st.session_state.get("voice_transcript", "")
    st.text_area(
        "Transcript",
        value=transcript,
        on_change=lambda: None,
        key="voice_chat_transcript",
        height=120,
    )

    if st.session_state.get("voice_segments"):
        with st.expander("Transcript segments", expanded=False):
            for seg in st.session_state.voice_segments:
                start = seg.get("start")
                end = seg.get("end")
                text = seg.get("text", "")
                st.markdown(f"- {start:.2f}s → {end:.2f}s: {text}")

    if st.button("Ask SentinelForge (voice)", key="voice_chat_send"):
        message = (st.session_state.voice_transcript or "").strip()
        if not message:
            st.warning("Transcript is empty. Upload audio and transcribe first.")
        else:
            dc = call_model("/api/chat", {"message": message})
            st.session_state.voice_chat_response = dc

    if resp := st.session_state.get("voice_chat_response"):
        st.success(
            resp.get("reply") or resp.get("answer") or resp.get("detail") or "Response received."
        )
        with st.expander("Full chat response", expanded=False):
            st.json(resp)

        reply_text = resp.get("reply") or resp.get("answer") or ""
        if reply_text:
            if st.button("Speak response", key="voice_chat_tts"):
                tts_bytes = _tts_playback(backend_url, reply_text, auth_headers)
                if tts_bytes:
                    st.session_state.voice_tts_audio = tts_bytes

    if audio := st.session_state.get("voice_tts_audio"):
        st.audio(audio, format="audio/wav")
