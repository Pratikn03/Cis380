"""UAIS-V Streamlit Chatbot for Recommendations."""
from __future__ import annotations

import json
import logging
import os

import sys
from pathlib import Path
import re
import uuid

from PIL import Image
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

from chatbot.context_manager import ContextManager
from streamlit_chatbot.recommender_router import route_recommendation
from agent.orchestrator import OmniChatXOrchestrator
from streamlit_chatbot.image_tags import extract_tags_from_image


st.set_page_config(page_title="UAIS-V Recommender Chatbot", page_icon="🤖", layout="wide")

logger = logging.getLogger(__name__)
context_manager = ContextManager()
risk_orchestrator = OmniChatXOrchestrator()


def parse_price_from_text(text: str) -> float | None:
    m = re.search(r"under\s*\$?(\d+)", text.lower())
    if m:
        return float(m.group(1))
    m2 = re.search(r"\$(\d+)", text.lower())
    if m2:
        return float(m2.group(1))
    return None


def extract_tags_from_query(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {t for t in tokens if len(t) > 2}


def compute_risk_note(items: list[dict]) -> str | None:
    if not items:
        return None
    item = items[0]
    price = float(re.sub(r"[^\d.]", "", item.get("price", "0") or "0"))
    rating = float(item.get("rating", 0))
    popularity = float(item.get("popularity", 0))
    try:
        # Prefer the orchestrator's public interface when possible.
        out = risk_orchestrator.handle(f"{price} {rating} {popularity}", user_id="streamlit", use_rag=False)
        if isinstance(out, dict):
            return str(out.get("answer") or out)
        return str(out)
    except Exception as exc:
        logger.warning("Risk overlay failed: %s", exc, exc_info=True)
        return "Risk overlay currently unavailable; please try again later."

# ---- Modern styling ----
st.markdown(
    """
    <style>
    .main {
        background: radial-gradient(circle at 20% 20%, #1f2937 0%, #0b132b 40%, #0b132b 100%);
        color: #e5e7eb;
        font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .theme-toggle {
        position: fixed;
        top: 16px;
        right: 16px;
        z-index: 1000;
    }
    .theme-btn {
        border-radius: 12px;
        padding: 6px 10px;
        border: 1px solid rgba(255,255,255,0.15);
        background: rgba(255,255,255,0.04);
        color: #e5e7eb;
        cursor: pointer;
    }
    .stChatInput > div > div {
        border-radius: 16px !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        background: rgba(255,255,255,0.04) !important;
        color: #e5e7eb !important;
    }
    .glass-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 12px 40px rgba(0,0,0,0.28);
    }
    .tag {
        display: inline-block;
        padding: 4px 10px;
        margin: 0 6px 6px 0;
        border-radius: 10px;
        background: rgba(255,255,255,0.08);
        color: #c7d2fe;
        font-size: 12px;
        border: 1px solid rgba(255,255,255,0.12);
    }
    h1, h2, h3, h4, h5, h6 { color: #f9fafb; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---- Header ----
st.markdown(
    """
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
        <div style="font-size:34px;">🤖</div>
        <div>
            <div style="font-size:30px;font-weight:700;letter-spacing:-0.02em;">UAIS-V Recommender Chatbot</div>
            <div style="color:#cbd5e1;font-size:14px;">Movies • Places • News (health/crime/general) — live APIs if available, fallbacks otherwise</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Theme toggle (visual only; demo switcher)
st.markdown(
    """
    <div class="theme-toggle">
        <button class="theme-btn" onclick="toggleTheme()">⚝ Theme</button>
    </div>
    <script>
    function toggleTheme() {
        const root = document.documentElement;
        const cur = root.style.getPropertyValue('--bg');
        // Simple CSS trick: invert background/text for demo
        const main = document.querySelector('.main');
        if (!main) return;
        const isDark = getComputedStyle(main).backgroundImage.includes('#0b132b');
        if (isDark) {
            main.style.background = 'linear-gradient(135deg, #f8fafc, #e2e8f0)';
            main.style.color = '#0f172a';
        } else {
            main.style.background = 'radial-gradient(circle at 20% 20%, #1f2937 0%, #0b132b 40%, #0b132b 100%)';
            main.style.color = '#e5e7eb';
        }
    }
    </script>
    """,
    unsafe_allow_html=True,
)

# Sidebar tips
st.sidebar.header("How to use")
st.sidebar.markdown(
    """
    - Ask for **movies**, **places**, or **news/health/crime** recommendations.
    - Examples:
      - "Recommend sci-fi movies"
      - "Best coffee shops in NYC"
      - "Latest health news"
      - "Crime news about NYC"
    - If API keys are missing, the bot will return curated fallbacks.
    """
)


def format_items(category: str, items: list[dict]) -> str:
    if not items:
        return f"No {category} results right now."
    lines = [f"Here are some {category.lower()} picks you might like:"]
    for i, it in enumerate(items, 1):
        title = it.get("title") or it.get("name") or "Item"
        reason = it.get("reason", "")
        url = it.get("url")
        location = it.get("location")
        overview = it.get("overview")
        bullet = f"{i}. **{title}**"
        details = []
        if reason:
            details.append(reason)
        if overview:
            details.append(overview)
        if location:
            details.append(location)
        if url:
            details.append(f"[Link]({url})")
        if details:
            bullet += " — " + " • ".join(details)
        lines.append(bullet)
    lines.append("Want more like this? Ask me for another topic or more options.")
    return "\n\n".join(lines)


def summarize_constraints(price_pref: float | None, tag_pref: set[str]) -> str | None:
    components: list[str] = []
    if price_pref and price_pref > 0:
        components.append(f"Budget ≤ ${price_pref:.0f}")
    if tag_pref:
        components.append(f"Tags: {', '.join(sorted(tag_pref))}")
    return " & ".join(components) if components else None


def domain_source_label(intent: str | None) -> str:
    mapping = {
        "movies": "Movie dataset",
        "places": "Places API / dataset",
        "news": "News feed",
        "news_health": "Health news feed",
        "news_crime": "Crime news feed",
        "phones": "Electronics catalog (CSV or curated fallback)",
        "laptops": "Electronics catalog (CSV or curated fallback)",
        "headphones": "Electronics catalog (CSV or curated fallback)",
        "courses": "Learning resources dataset",
        "clothes": "Clothes handler",
    }
    if not intent:
        return "OmniChatX knowledge sources"
    return mapping.get(intent, "OmniChatX knowledge sources")


def main():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    # Backward-compatible backend URL env var.
    # README uses OMNICHATX_BACKEND; older docs used OMNINEX_BACKEND.
    backend_url = os.environ.get("OMNICHATX_BACKEND") or os.environ.get("OMNINEX_BACKEND", "http://localhost:8000")

    def call_model(path: str, payload: dict) -> dict:
        try:
            headers: dict[str, str] = {}
            if os.getenv("AUTH_TOKEN"):
                headers["Authorization"] = f"Bearer {os.environ['AUTH_TOKEN']}"
            resp = requests.post(f"{backend_url}{path}", json=payload, headers=headers, timeout=10.0)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            return {"error": f"{exc}"}

    def call_upload(path: str, *, filename: str, content: bytes, content_type: str) -> dict:
        try:
            headers: dict[str, str] = {}
            if os.getenv("AUTH_TOKEN"):
                headers["Authorization"] = f"Bearer {os.environ['AUTH_TOKEN']}"
            files = {"file": (filename, content, content_type)}
            resp = requests.post(f"{backend_url}{path}", files=files, headers=headers, timeout=30.0)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            return {"error": f"{exc}"}

    tabs = st.tabs(["Chat & Recommendations", "OmniChatX Agent", "Voice & Vision", "Risk & Anomaly"])

    with tabs[0]:
        # Image upload section
        st.sidebar.subheader("Upload an image for style-based suggestions")
        uploaded = st.sidebar.file_uploader("Choose an image", type=["png", "jpg", "jpeg"])
        image_tags_text = ""
        if uploaded:
            try:
                img = Image.open(uploaded).convert("RGB")
                tags = extract_tags_from_image(img, top_k=5)
                if tags:
                    image_tags_text = " ".join(tags)
                    st.sidebar.success(f"Detected tags: {', '.join(tags)}")
                else:
                    st.sidebar.warning("No tags detected.")
            except Exception as exc:
                st.sidebar.error(f"Image processing failed: {exc}")

        # Suggestions bar
        st.markdown(
            """
            <div class="glass-card" style="margin: 12px 0;">
                <div style="color:#e5e7eb;font-size:14px;margin-bottom:6px;">Try asking:</div>
                <div>
                    <span class="tag">Recommend sci-fi movies</span>
                    <span class="tag">Best coffee shops in NYC</span>
                    <span class="tag">Latest health news</span>
                    <span class="tag">Outfit ideas for a 30 year old</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        def _process_query(text: str, tag_source: str) -> None:
            clean_query = " ".join(filter(None, [text, tag_source])).strip()
            if not clean_query:
                return
            st.session_state.messages.append({"role": "user", "content": clean_query})
            with st.chat_message("user"):
                st.markdown(clean_query)

            price_pref = parse_price_from_text(clean_query)
            tag_pref = extract_tags_from_query(clean_query)
            preference_payload = {"price": price_pref, "preferred_tags": tag_pref}

            try:
                rec = route_recommendation(clean_query, preference=preference_payload)
                context_manager.update(
                    st.session_state.session_id,
                    last_intent=rec.get("intent"),
                    last_user_message=clean_query,
                    price_preference=price_pref,
                    preferred_tags=list(tag_pref),
                )
                st.session_state.preference = preference_payload
                reply = format_items(rec["category"], rec["items"])
                risk_note = compute_risk_note(rec["items"])
            except Exception as exc:
                reply = f"Error: {exc}"
                risk_note = None
                rec = {"items": [], "category": "Results"}

            with st.chat_message("assistant"):
                st.markdown(reply)
                tradeoff_note = None
                if rec["items"]:
                    tradeoff_note = rec["items"][0].get("tradeoff")
                constraints = summarize_constraints(price_pref, tag_pref)
                source_label = domain_source_label(rec.get("intent"))
                if tradeoff_note:
                    st.caption(f"Tradeoff note: {tradeoff_note}")
                if constraints:
                    st.caption(f"Constraints applied: {constraints}")
                if source_label:
                    st.caption(f"Source: {source_label}")
                if risk_note:
                    st.info(f"Risk overlay: {risk_note}")
            st.session_state.messages.append({"role": "assistant", "content": reply})

        general_filters = [
            ("Romantic movies", "Recommend a romantic movie"),
            ("Top NYC coffee shops", "Best coffee shops in NYC"),
            ("Latest health news", "Latest health news"),
            ("Crime update", "Crime news about San Francisco"),
        ]
        cols = st.columns(len(general_filters))
        for col, (label, query) in zip(cols, general_filters):
            if col.button(label):
                _process_query(query, image_tags_text)

        # Manual input box + send button (more reliable than chat_input)
        user_input = st.text_input("Ask for movies, places, or news (health/crime)...", key="manual_query")
        send = st.button("Send", type="primary")
        if send and user_input.strip():
            _process_query(user_input.strip(), image_tags_text)

        quick_filters = [
            ("Budget phones", "Recommend budget phones under $600"),
            ("Programming laptops", "Recommend laptops for programming under $1200"),
            ("Noise-canceling headphones", "Recommend noise cancelling headphones"),
        ]
        cols = st.columns(len(quick_filters))
        for col, (label, query) in zip(cols, quick_filters):
            if col.button(label):
                _process_query(query, image_tags_text)

    with tabs[1]:
        st.markdown("### OmniChatX Agent Chat")
        st.caption(
            "This calls the backend `/api/chat`. For GPT-like answers, set `OPENAI_API_KEY` in your environment. "
            "You can also attach an audio clip or image; their predictions are appended to your prompt as context."
        )

        if "agent_messages" not in st.session_state:
            st.session_state.agent_messages = []

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            agent_audio = st.file_uploader(
                "Attach audio (optional)",
                type=["wav", "mp3", "m4a", "aac", "ogg"],
                key="agent_audio_upload",
            )
        with col_b:
            agent_image = st.file_uploader(
                "Attach image (optional)",
                type=["png", "jpg", "jpeg", "webp"],
                key="agent_image_upload",
            )
        with col_c:
            agent_video = st.file_uploader(
                "Attach video (optional)",
                type=["mp4", "mov", "avi", "mkv"],
                key="agent_video_upload",
            )

        for msg in st.session_state.agent_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        agent_text = st.text_input("Ask anything (agent chat)…", key="agent_query")
        if st.button("Send to agent", key="agent_send", type="primary") and agent_text.strip():
            user_text = agent_text.strip()
            st.session_state.agent_messages.append({"role": "user", "content": user_text})
            with st.chat_message("user"):
                st.markdown(user_text)

            context_lines: list[str] = []
            if agent_audio is not None:
                voice_res = call_upload(
                    "/api/voice/emotion",
                    filename=agent_audio.name,
                    content=agent_audio.getvalue(),
                    content_type=agent_audio.type or "audio/wav",
                )
                if "error" in voice_res:
                    context_lines.append(f"[voice] error: {voice_res['error']}")
                else:
                    context_lines.append(
                        f"[voice] emotion={voice_res.get('emotion')} confidence={voice_res.get('confidence')}"
                    )

            if agent_image is not None:
                vision_res = call_upload(
                    "/api/vision/predict",
                    filename=agent_image.name,
                    content=agent_image.getvalue(),
                    content_type=agent_image.type or "image/jpeg",
                )
                if "error" in vision_res:
                    context_lines.append(f"[vision] error: {vision_res['error']}")
                else:
                    context_lines.append(
                        f"[vision] label={vision_res.get('label')} confidence={vision_res.get('confidence')}"
                    )

            if agent_video is not None:
                video_res = call_upload(
                    "/api/vision/video/predict?fps=1&max_frames=25",
                    filename=agent_video.name,
                    content=agent_video.getvalue(),
                    content_type=agent_video.type or "video/mp4",
                )
                if "error" in video_res:
                    context_lines.append(f"[vision] video error: {video_res['error']}")
                else:
                    context_lines.append(
                        f"[vision] label={video_res.get('label')} confidence={video_res.get('confidence')} (video)"
                    )

            prompt = user_text
            if context_lines:
                prompt += "\n\nContext:\n" + "\n".join(context_lines)

            chat_res = call_model("/api/chat", {"message": prompt})
            if "error" in chat_res:
                reply_text = chat_res["error"]
            else:
                reply_text = chat_res.get("reply") or chat_res.get("answer") or json.dumps(chat_res, indent=2)

            with st.chat_message("assistant"):
                st.markdown(reply_text)
                if context_lines:
                    st.caption("Context attached: " + " | ".join(context_lines))
            st.session_state.agent_messages.append({"role": "assistant", "content": reply_text})

    with tabs[2]:
        st.markdown("### Live Capture (No Uploads)")
        st.write("Use your microphone/webcam directly. The app sends the captured media to your local backend for inference.")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### Microphone (record → analyze)")
            mic_audio = st.audio_input("Record audio", key="voice_mic_input")
            if mic_audio is not None:
                if st.button("Analyze recorded audio", key="voice_mic_analyze", type="primary"):
                    result = call_upload(
                        "/api/voice/emotion",
                        filename=mic_audio.name or "mic.wav",
                        content=mic_audio.getvalue(),
                        content_type=mic_audio.type or "audio/wav",
                    )
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.success("Voice emotion detected")
                        st.json(result)

        with col_b:
            st.markdown("#### Webcam (snapshot → predict)")
            cam_img = st.camera_input("Take a photo", key="vision_cam_input")
            if cam_img is not None:
                st.image(cam_img, caption=cam_img.name, use_container_width=True)
                if st.button("Predict snapshot", key="vision_cam_predict", type="primary"):
                    result = call_upload(
                        "/api/vision/predict",
                        filename=cam_img.name or "webcam.jpg",
                        content=cam_img.getvalue(),
                        content_type=cam_img.type or "image/jpeg",
                    )
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.success("Vision prediction complete")
                        st.json(result)

        st.divider()

        st.markdown("### Real-Time (Mic + Webcam) — Optional")
        st.write(
            "For continuous live updates (like a real-time demo), enable WebRTC streaming. "
            "This is optional and requires extra dependencies."
        )
        enable_webrtc = st.checkbox(
            "Enable real-time streaming (requires `streamlit-webrtc`)",
            value=False,
            key="enable_webrtc_realtime",
        )
        if enable_webrtc:
            try:
                import io
                import threading
                import time
                import wave
                from dataclasses import dataclass, field

                import numpy as np
                from PIL import Image, ImageDraw

                from streamlit_webrtc import (
                    AudioProcessorBase,
                    RTCConfiguration,
                    VideoProcessorBase,
                    WebRtcMode,
                    webrtc_streamer,
                )
            except Exception as exc:
                st.error(
                    "Real-time streaming dependencies are missing.\n\n"
                    "Install (recommended in a Python 3.11+ venv):\n"
                    "`pip install streamlit-webrtc av aiortc`\n\n"
                    f"Import error: {exc}"
                )
            else:

                @dataclass
                class _RealtimeState:
                    lock: threading.Lock = field(default_factory=threading.Lock)
                    vision_label: str | None = None
                    vision_confidence: float | None = None
                    voice_emotion: str | None = None
                    voice_confidence: float | None = None
                    last_vision_raw: dict | None = None
                    last_voice_raw: dict | None = None

                    def snapshot(self) -> dict[str, object]:
                        with self.lock:
                            return {
                                "vision_label": self.vision_label,
                                "vision_confidence": self.vision_confidence,
                                "voice_emotion": self.voice_emotion,
                                "voice_confidence": self.voice_confidence,
                            }

                    def update_vision(self, payload: dict) -> None:
                        with self.lock:
                            self.vision_label = payload.get("label") or payload.get("prediction")
                            self.vision_confidence = payload.get("confidence")
                            self.last_vision_raw = payload

                    def update_voice(self, payload: dict) -> None:
                        with self.lock:
                            self.voice_emotion = payload.get("emotion")
                            self.voice_confidence = payload.get("confidence")
                            self.last_voice_raw = payload

                if "webrtc_rt_state" not in st.session_state:
                    st.session_state.webrtc_rt_state = _RealtimeState()
                rt_state: _RealtimeState = st.session_state.webrtc_rt_state

                def _headers() -> dict[str, str]:
                    if os.getenv("AUTH_TOKEN"):
                        return {"Authorization": f"Bearer {os.environ['AUTH_TOKEN']}"}
                    return {}

                def _encode_jpeg(rgb: "np.ndarray") -> bytes:
                    buf = io.BytesIO()
                    Image.fromarray(rgb).save(buf, format="JPEG", quality=85)
                    return buf.getvalue()

                def _pcm16_to_wav_bytes(pcm16: "np.ndarray", sr: int) -> bytes:
                    pcm16 = np.asarray(pcm16, dtype=np.int16)
                    buf = io.BytesIO()
                    with wave.open(buf, "wb") as w:
                        w.setnchannels(1)
                        w.setsampwidth(2)
                        w.setframerate(int(sr))
                        w.writeframes(pcm16.tobytes())
                    return buf.getvalue()

                def _safe_float(x) -> float | None:
                    try:
                        return None if x is None else float(x)
                    except Exception:
                        return None

                class _RealtimeVideoProcessor(VideoProcessorBase):
                    def __init__(self) -> None:
                        self._last_sent = 0.0
                        self._inflight = False

                    def _infer(self, jpeg_bytes: bytes) -> None:
                        nonlocal backend_url
                        try:
                            files = {"file": ("frame.jpg", jpeg_bytes, "image/jpeg")}
                            resp = requests.post(
                                f"{backend_url}/api/vision/predict",
                                files=files,
                                headers=_headers(),
                                timeout=20,
                            )
                            resp.raise_for_status()
                            payload = resp.json()
                            rt_state.update_vision(payload)
                        except Exception:
                            # Keep the stream alive even if inference fails.
                            pass
                        finally:
                            self._inflight = False

                    def recv(self, frame):
                        import av  # local import (required by streamlit-webrtc)

                        rgb = frame.to_ndarray(format="rgb24")
                        now = time.monotonic()
                        if (now - self._last_sent) >= 1.0 and not self._inflight:
                            self._last_sent = now
                            self._inflight = True
                            jpeg = _encode_jpeg(rgb)
                            threading.Thread(target=self._infer, args=(jpeg,), daemon=True).start()

                        snap = rt_state.snapshot()
                        img = Image.fromarray(rgb)
                        draw = ImageDraw.Draw(img)
                        v_label = snap.get("vision_label") or "…"
                        v_conf = _safe_float(snap.get("vision_confidence"))
                        a_label = snap.get("voice_emotion") or "…"
                        a_conf = _safe_float(snap.get("voice_confidence"))
                        text = f"vision: {v_label} ({'' if v_conf is None else f'{v_conf:.2f}'})  |  voice: {a_label} ({'' if a_conf is None else f'{a_conf:.2f}'})"
                        draw.rectangle((0, 0, 1100, 36), fill=(0, 0, 0))
                        draw.text((10, 10), text, fill=(255, 255, 255))
                        return av.VideoFrame.from_ndarray(np.array(img), format="rgb24")

                class _RealtimeAudioProcessor(AudioProcessorBase):
                    def __init__(self) -> None:
                        self._buf = np.zeros((0,), dtype=np.int16)
                        self._sr = 16000
                        self._last_sent = 0.0
                        self._inflight = False

                    def _infer(self, wav_bytes: bytes) -> None:
                        nonlocal backend_url
                        try:
                            files = {"file": ("live.wav", wav_bytes, "audio/wav")}
                            resp = requests.post(
                                f"{backend_url}/api/voice/emotion",
                                files=files,
                                headers=_headers(),
                                timeout=30,
                            )
                            resp.raise_for_status()
                            payload = resp.json()
                            rt_state.update_voice(payload)
                        except Exception:
                            pass
                        finally:
                            self._inflight = False

                    def recv(self, frame):
                        import av  # local import (required by streamlit-webrtc)

                        arr = frame.to_ndarray()
                        try:
                            self._sr = int(getattr(frame, "sample_rate", None) or self._sr)
                        except Exception:
                            pass

                        pcm = arr
                        if pcm.ndim == 2:
                            # Handle both (channels, samples) and (samples, channels)
                            if pcm.shape[0] <= 2 and pcm.shape[1] > pcm.shape[0]:
                                pcm = pcm.mean(axis=0)
                            else:
                                pcm = pcm.mean(axis=1)
                        pcm = np.asarray(pcm)

                        if np.issubdtype(pcm.dtype, np.floating):
                            pcm = np.clip(pcm, -1.0, 1.0)
                            pcm16 = (pcm * 32767.0).astype(np.int16)
                        else:
                            pcm16 = pcm.astype(np.int16, copy=False)

                        self._buf = np.concatenate([self._buf, pcm16])

                        # Keep only the last ~3 seconds.
                        max_keep = int(max(1, self._sr) * 3)
                        if self._buf.size > max_keep:
                            self._buf = self._buf[-max_keep:]

                        now = time.monotonic()
                        if (
                            not self._inflight
                            and (now - self._last_sent) >= 1.2
                            and self._buf.size >= int(max(1, self._sr) * 1)
                        ):
                            self._last_sent = now
                            self._inflight = True
                            window = self._buf[-int(self._sr * 1) :]
                            wav_bytes = _pcm16_to_wav_bytes(window, self._sr)
                            threading.Thread(target=self._infer, args=(wav_bytes,), daemon=True).start()

                        return frame

                st.caption(f"Backend target: `{backend_url}` (start it with `uvicorn backend.main:app --port 8000`).")
                webrtc_streamer(
                    key="omnichatx_realtime_webrtc",
                    mode=WebRtcMode.SENDRECV,
                    rtc_configuration=RTCConfiguration({"iceServers": []}),
                    media_stream_constraints={"video": True, "audio": True},
                    video_processor_factory=_RealtimeVideoProcessor,
                    audio_processor_factory=_RealtimeAudioProcessor,
                    async_processing=True,
                )

        st.divider()

        st.markdown("### Voice Emotion Detection")
        st.write("Upload a short WAV/MP3/M4A clip and get an emotion label + confidence.")

        audio_file = st.file_uploader(
            "Audio file",
            type=["wav", "mp3", "m4a", "aac", "ogg"],
            key="voice_upload",
        )
        if audio_file is not None:
            if st.button("Detect voice emotion", type="primary"):
                result = call_upload(
                    "/api/voice/emotion",
                    filename=audio_file.name,
                    content=audio_file.getvalue(),
                    content_type=audio_file.type or "audio/wav",
                )
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success("Voice emotion detected")
                    st.json(result)

        st.divider()

        st.markdown("### Vision (Image) Prediction")
        st.write("Upload an image to run the trained vision model (real/fake or multi-class, depending on your dataset).")

        image_file = st.file_uploader(
            "Image file",
            type=["png", "jpg", "jpeg", "webp"],
            key="vision_upload",
        )
        if image_file is not None:
            st.image(image_file, caption=image_file.name, use_container_width=True)
            if st.button("Predict image label"):
                result = call_upload(
                    "/api/vision/predict",
                    filename=image_file.name,
                    content=image_file.getvalue(),
                    content_type=image_file.type or "image/jpeg",
                )
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success("Vision prediction complete")
                    st.json(result)

        st.divider()

        st.markdown("### Vision (Video) Prediction")
        st.write("Upload a short video; the backend samples frames and averages per-frame probabilities.")

        vid_file = st.file_uploader(
            "Video file",
            type=["mp4", "mov", "avi", "mkv"],
            key="vision_video_upload",
        )
        fps = st.number_input("Frame sampling FPS", min_value=0.1, max_value=10.0, value=1.0, step=0.5)
        max_frames = st.number_input("Max frames to analyze", min_value=1, max_value=200, value=30, step=5)
        if vid_file is not None:
            if st.button("Predict video", key="vision_video_predict"):
                path = f"/api/vision/video/predict?fps={float(fps)}&max_frames={int(max_frames)}"
                result = call_upload(
                    path,
                    filename=vid_file.name,
                    content=vid_file.getvalue(),
                    content_type=vid_file.type or "video/mp4",
                )
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success("Video prediction complete")
                    st.json(result)

    with tabs[3]:
        st.markdown("### Risk & Anomaly Explorer")
        st.write(
            "Send numeric features to the fraud, cyber, or behavior model endpoints and view the returned"
            " scores/explanations. Features should match the order expected by the deployed models."
        )

        def render_form(title: str, endpoint: str, key: str):
            st.subheader(title)
            features_input = st.text_area(
                f"Features (comma-separated numbers for {title.lower()})",
                value="0, 0, 0, 0, 0, 0, 0, 0",
                key=f"{key}_features",
                height=80,
            )
            submitted = st.button(f"Score {title}", key=f"{key}_submit")
            if submitted:
                try:
                    values = [float(x.strip()) for x in features_input.split(",") if x.strip()]
                except ValueError:
                    st.error("Please provide only numbers, separated by commas.")
                    return
                payload = {"features": values}
                result = call_model(endpoint, payload)
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success(f"{title} score returned")
                    st.json(result)

        render_form("Fraud", "/api/fraud", "fraud")
        render_form("Cyber", "/api/cyber", "cyber")
        render_form("Behavior", "/api/behavior", "behavior")


if __name__ == "__main__":
    main()
