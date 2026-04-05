from __future__ import annotations

from typing import Callable

import streamlit as st

from ..utils import call_with_container_width


def render_live_page(
    *,
    backend_url: str,
    call_multipart: Callable[..., dict],
    auth_headers: Callable[[], dict[str, str]],
) -> None:
    """Live mic + webcam page.

    Design goals:
    - Snapshot-first (works everywhere)
    - WebRTC optional and clearly gated
    - Avoid long blocking loops; only send on user action or periodic tick
    """

    st.markdown("## Live (Mic + Webcam)")
    st.caption("Snapshot mode works everywhere. Real-time mode uses WebRTC when installed.")

    top = st.columns([1, 1, 1])
    with top[0]:
        st.markdown(
            '<div class="metric-card"><div class="muted">Backend</div><div style="font-weight:700;">%s</div></div>'
            % backend_url,
            unsafe_allow_html=True,
        )
    with top[1]:
        st.markdown(
            '<div class="metric-card"><div class="muted">Endpoint</div><div style="font-weight:700;">/api/chat/multimodal</div></div>',
            unsafe_allow_html=True,
        )
    with top[2]:
        st.markdown(
            '<div class="metric-card"><div class="muted">Mode</div><div style="font-weight:700;">Snapshot + WebRTC (optional)</div></div>',
            unsafe_allow_html=True,
        )

    st.divider()

    snap_col1, snap_col2 = st.columns(2)
    with snap_col1:
        st.markdown("### Microphone (snapshot)")
        mic_audio = st.audio_input("Record audio", key="live_mic_snapshot")
    with snap_col2:
        st.markdown("### Webcam (snapshot)")
        cam_img = st.camera_input("Take a photo", key="live_cam_snapshot")

    use_stt = st.checkbox(
        "Use speech-to-text (STT) from microphone (no typing required)",
        value=False,
        key="live_use_stt",
    )
    stt_language = st.text_input(
        "STT language (optional, e.g. en)", value="", key="live_stt_language"
    )

    live_text = st.text_input(
        "Instruction (optional)" if use_stt else "Message",
        value="Explain what you detect." if not use_stt else "",
        key="live_prompt",
    )
    user_id = st.text_input("User id", value="streamlit", key="live_user_id")
    use_rag = st.checkbox("Use RAG", value=True, key="live_use_rag")

    if "live_last" not in st.session_state:
        st.session_state.live_last = None

    col_run, col_clear = st.columns([1, 1])
    with col_run:
        run_once = st.button("Run multimodal chat", key="live_run_once", type="primary")
    with col_clear:
        if st.button("Clear last result", key="live_clear"):
            st.session_state.live_last = None

    if run_once:
        upload_files: dict[str, tuple[str, bytes, str]] = {}
        if mic_audio is not None:
            upload_files["audio"] = (
                mic_audio.name or "mic.wav",
                mic_audio.getvalue(),
                mic_audio.type or "audio/wav",
            )
        if cam_img is not None:
            upload_files["image"] = (
                cam_img.name or "webcam.jpg",
                cam_img.getvalue(),
                cam_img.type or "image/jpeg",
            )

        message = (live_text or "").strip()
        instruction = ""
        if use_stt:
            instruction = message
            message = ""
        if not use_stt and not message:
            message = "Analyze the input."

        res = call_multipart(
            "/api/chat/multimodal",
            data={
                "message": message,
                "instruction": instruction,
                "user_id": user_id,
                "use_rag": "true" if use_rag else "false",
                "transcribe_audio": "true" if use_stt else "false",
                "stt_language": (stt_language or "").strip(),
            },
            files=upload_files or None,
            timeout=120.0,
        )
        st.session_state.live_last = res

    if st.session_state.live_last is not None:
        res = st.session_state.live_last
        if isinstance(res, dict) and "error" in res:
            st.error(res["error"])
        else:
            st.success((res or {}).get("reply") or (res or {}).get("answer") or "Done")
            with st.expander("Full response", expanded=False):
                st.json(res)

    st.divider()

    st.markdown("### Real-time (WebRTC) — optional")
    enable_webrtc = st.checkbox(
        "Enable real-time streaming (requires streamlit-webrtc)",
        value=False,
        key="enable_webrtc_realtime",
    )

    if not enable_webrtc:
        st.caption("Tip: Snapshot mode is the most stable across environments.")
        return

    if "webrtc_streaming" not in st.session_state:
        st.session_state.webrtc_streaming = False
    if "webrtc_last_frame" not in st.session_state:
        st.session_state.webrtc_last_frame = None
    if "webrtc_last_response" not in st.session_state:
        st.session_state.webrtc_last_response = None
    if "webrtc_last_sent" not in st.session_state:
        st.session_state.webrtc_last_sent = 0.0

    control_col, status_col, preview_col = st.columns([1, 2, 1])
    with control_col:
        start_btn = st.button("Start streaming", key="webrtc_start", type="primary")
        stop_btn = st.button("Stop streaming", key="webrtc_stop", type="secondary")
    with status_col:
        status_placeholder = st.empty()
        if st.session_state.webrtc_streaming:
            status_placeholder.success("Streaming active • sending every few seconds")
        else:
            status_placeholder.info("Streaming paused • click Start to capture")
    with preview_col:
        st.caption("Latest preview")
        if st.session_state.webrtc_last_frame is not None:
            st.image(st.session_state.webrtc_last_frame, use_column_width=True)
        else:
            st.markdown("No frame captured yet.")

    if start_btn:
        st.session_state.webrtc_streaming = True
    if stop_btn:
        st.session_state.webrtc_streaming = False

    if not st.session_state.webrtc_streaming:
        if st.session_state.webrtc_last_response is not None:
            with st.expander("Last response", expanded=False):
                st.json(st.session_state.webrtc_last_response)
        st.caption("Resume streaming when you're ready.")
        return

    try:
        import queue
        import time
        import io
        import wave

        import numpy as np  # type: ignore
        from streamlit_webrtc import WebRtcMode, webrtc_streamer, RTCConfiguration  # type: ignore

        st.info(
            "Streaming is active. We'll sample audio/video and call `/api/chat/multimodal` every interval."
        )

        interval_s = st.slider("Send interval (seconds)", 0.5, 8.0, 2.0, 0.5)
        max_audio_frames = st.slider("Audio frames per batch", 5, 80, 20, 5)

        webrtc_ctx = webrtc_streamer(
            key="uaisv_live_webrtc",
            mode=WebRtcMode.SENDONLY,
            rtc_configuration=RTCConfiguration({"iceServers": []}),
            media_stream_constraints={"video": True, "audio": True},
            video_receiver_size=4,
            audio_receiver_size=256,
            async_processing=True,
        )

        now = time.time()
        if now - float(st.session_state.webrtc_last_sent) < float(interval_s):
            st.caption("Waiting for the next send window…")
            if st.session_state.webrtc_last_response is not None:
                with st.expander("Latest response", expanded=False):
                    st.json(st.session_state.webrtc_last_response)
            return

        st.session_state.webrtc_last_sent = now

        image_bytes = None
        if webrtc_ctx.video_receiver:
            try:
                vf = webrtc_ctx.video_receiver.get_frame(timeout=1)
                img_rgb = vf.to_ndarray(format="rgb24")
                st.session_state.webrtc_last_frame = img_rgb
                frame_preview = st.empty()
                call_with_container_width(frame_preview.image, img_rgb, caption="Live preview")
                buf = io.BytesIO()
                import PIL.Image  # type: ignore

                PIL.Image.fromarray(img_rgb).save(buf, format="JPEG", quality=85)
                image_bytes = buf.getvalue()
            except queue.Empty:
                pass
            except Exception:
                pass

        wav_bytes = None
        if webrtc_ctx.audio_receiver:
            try:
                audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=1)
                audio_frames = audio_frames[-int(max_audio_frames) :]
                if audio_frames:
                    pcm = []
                    sr = audio_frames[-1].sample_rate
                    for fr in audio_frames:
                        arr = fr.to_ndarray()
                        if arr.ndim == 2:
                            arr = arr.mean(axis=0)
                        if arr.dtype.kind == "f":
                            arr = np.clip(arr, -1.0, 1.0) * 32767.0
                        pcm.append(arr.astype(np.int16))
                    pcm_i16 = np.concatenate(pcm) if pcm else None
                    if pcm_i16 is not None and pcm_i16.size > 0:
                        out = io.BytesIO()
                        with wave.open(out, "wb") as wf:
                            wf.setnchannels(1)
                            wf.setsampwidth(2)
                            wf.setframerate(int(sr))
                            wf.writeframes(pcm_i16.tobytes())
                        wav_bytes = out.getvalue()
            except Exception:
                wav_bytes = None

        upload_files2: dict[str, tuple[str, bytes, str]] = {}
        if image_bytes is not None:
            upload_files2["image"] = ("webcam.jpg", image_bytes, "image/jpeg")
        if wav_bytes is not None:
            upload_files2["audio"] = ("mic.wav", wav_bytes, "audio/wav")

        rt_message = (live_text or "").strip()
        rt_instruction = ""
        if use_stt:
            rt_instruction = rt_message
            rt_message = ""
        if not use_stt and not rt_message:
            rt_message = "Analyze the stream."

        res = call_multipart(
            "/api/chat/multimodal",
            data={
                "message": rt_message,
                "instruction": rt_instruction,
                "user_id": user_id,
                "use_rag": "true" if use_rag else "false",
                "transcribe_audio": "true" if use_stt else "false",
                "stt_language": (stt_language or "").strip(),
            },
            files=upload_files2 or None,
            timeout=120.0,
        )
        st.session_state.webrtc_last_response = res

        if isinstance(res, dict) and "error" in res:
            st.error(res["error"])
        else:
            with st.expander("Latest response", expanded=False):
                st.json(res)

        st.caption(
            "Tip: Streamlit reruns drive the periodic sends. Keep this tab focused for best results."
        )

    except Exception as exc:
        st.warning(
            "WebRTC dependencies aren’t installed (or failed to import). "
            "Snapshot mode above still works.\n\n"
            f"Details: {exc}"
        )
