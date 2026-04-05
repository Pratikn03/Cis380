"""
Sentifargo - Unified Chat Interface
Complete all-in-one assistant with:
- Unified layout with bluish-gray background
- Fraud/Cyber/Behavior detection
- Vision & Video analysis
- Voice emotion analysis
- Recommendations (movies, products, courses, news)
- RAG document chat
- Live agent interaction
"""

from __future__ import annotations

import os
import sys
import uuid
import html
import logging
import traceback
from pathlib import Path
from typing import Callable
from datetime import datetime

import requests
import streamlit as st

from .utils import call_with_container_width

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File size limits (in bytes)
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB
MAX_AUDIO_SIZE = 20 * 1024 * 1024  # 20MB
MAX_MESSAGE_LENGTH = 5000

# Setup paths
THIS_DIR = Path(__file__).resolve().parent
APP_ROOT = THIS_DIR.parent
REPO_ROOT = THIS_DIR.parents[1]
SRC_DIR = REPO_ROOT / "src"

desired_sys_path = [str(REPO_ROOT), str(SRC_DIR), str(APP_ROOT)]
for p in desired_sys_path:
    while p in sys.path:
        sys.path.remove(p)
sys.path.insert(0, desired_sys_path[0])
sys.path.insert(1, desired_sys_path[1])
sys.path.insert(2, desired_sys_path[2])


def render_unified_chat(
    *,
    backend_url: str,
    call_model: Callable[..., dict],
    call_multipart: Callable[..., dict],
    call_get: Callable[..., dict],
    auth_headers: Callable[[], dict[str, str]],
) -> None:
    """Render the unified Sentinel interface."""

    # Custom CSS - unified chat theme with bluish-gray palette
    st.markdown(
        """
    <style>
    /* Global background and theme */
    .stApp {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d3e50 25%, #1a252f 50%, #0f1419 100%);
    }
    
    /* Main container */
    .main {
        background: transparent;
    }
    
    /* Hide default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Top header styling */
    .sentinel-header {
        background: linear-gradient(135deg, rgba(30, 58, 95, 0.9) 0%, rgba(26, 37, 47, 0.95) 100%);
        backdrop-filter: blur(10px);
        border-bottom: 2px solid rgba(59, 130, 246, 0.3);
        padding: 20px 40px;
        margin: -70px -100px 30px -100px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        position: sticky;
        top: 0;
        z-index: 999;
    }
    
    .sentinel-title {
        font-size: 42px;
        font-weight: 700;
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 50%, #2563eb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        text-align: center;
        letter-spacing: -0.5px;
    }
    
    .sentinel-subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 14px;
        margin-top: 8px;
        letter-spacing: 2px;
    }
    
    /* Chat container */
    .chat-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 20px;
    }
    
    /* Message bubbles - unified chat style */
    .message-row {
        display: flex;
        margin: 16px 0;
        align-items: flex-start;
        gap: 12px;
    }
    
    .message-row.user {
        justify-content: flex-end;
    }
    
    .message-row.assistant {
        justify-content: flex-start;
    }
    
    .message-avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        flex-shrink: 0;
    }
    
    .message-avatar.user {
        background: linear-gradient(135deg, #f59e0b, #d97706);
    }
    
    .message-avatar.assistant {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
    }
    
    .message-content {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 18px;
        padding: 14px 18px;
        max-width: 75%;
        color: #e2e8f0;
        line-height: 1.6;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
    }
    
    .message-row.user .message-content {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.25), rgba(37, 99, 235, 0.25));
        border-color: rgba(59, 130, 246, 0.4);
    }
    
    .message-row.assistant .message-content {
        background: rgba(30, 41, 59, 0.6);
        border-color: rgba(148, 163, 184, 0.3);
    }
    
    /* Attachment indicators */
    .attachment-badge {
        display: inline-block;
        padding: 4px 10px;
        margin: 6px 6px 0 0;
        border-radius: 12px;
        background: rgba(59, 130, 246, 0.2);
        border: 1px solid rgba(59, 130, 246, 0.4);
        color: #60a5fa;
        font-size: 11px;
        font-weight: 500;
    }
    
    /* Input area styling */
    .input-section {
        background: rgba(30, 41, 59, 0.8);
        backdrop-filter: blur(12px);
        border-top: 2px solid rgba(59, 130, 246, 0.3);
        padding: 20px;
        margin: 30px -100px -100px -100px;
        box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.4);
    }
    
    /* Sidebar styling */
    .css-1d391kg, section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(15, 23, 42, 0.95) 0%, rgba(15, 20, 28, 0.98) 100%);
        backdrop-filter: blur(10px);
    }
    
    .sidebar-section {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.5);
        transform: translateY(-2px);
    }
    
    /* File uploader */
    .stFileUploader {
        background: rgba(30, 41, 59, 0.4);
        border: 1px dashed rgba(148, 163, 184, 0.3);
        border-radius: 10px;
        padding: 10px;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 8px;
        color: #e2e8f0;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(30, 41, 59, 0.5);
        border-radius: 10px;
        padding: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: #94a3b8;
        border: 1px solid transparent;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.3), rgba(37, 99, 235, 0.3));
        border-color: rgba(59, 130, 246, 0.5);
        color: #60a5fa;
    }
    
    /* Metrics */
    .metric-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #60a5fa;
    }
    
    .metric-label {
        font-size: 12px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 4px;
    }
    
    /* Typing indicator */
    .typing-indicator {
        display: flex;
        gap: 6px;
        padding: 12px;
    }
    
    .typing-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #60a5fa;
        animation: typing-pulse 1.4s infinite ease-in-out;
    }
    
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes typing-pulse {
        0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
        40% { opacity: 1; transform: scale(1.2); }
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-badge.success {
        background: rgba(34, 197, 94, 0.2);
        border: 1px solid rgba(34, 197, 94, 0.4);
        color: #4ade80;
    }
    
    .status-badge.warning {
        background: rgba(251, 191, 36, 0.2);
        border: 1px solid rgba(251, 191, 36, 0.4);
        color: #fbbf24;
    }
    
    .status-badge.error {
        background: rgba(239, 68, 68, 0.2);
        border: 1px solid rgba(239, 68, 68, 0.4);
        color: #f87171;
    }
    
    .status-badge.info {
        background: rgba(59, 130, 246, 0.2);
        border: 1px solid rgba(59, 130, 246, 0.4);
        color: #60a5fa;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(15, 23, 42, 0.5);
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(59, 130, 246, 0.5);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(59, 130, 246, 0.7);
    }
    
    /* Feature icons */
    .feature-icon {
        font-size: 24px;
        margin-right: 8px;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .sentinel-header {
            padding: 15px 20px;
            margin: -70px -20px 20px -20px;
        }
        
        .sentinel-title {
            font-size: 28px;
        }
        
        .message-content {
            max-width: 85%;
        }
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Header
    st.markdown(
        """
    <div class="sentinel-header">
        <h1 class="sentinel-title">🧠 Sentifargo</h1>
        <div class="sentinel-subtitle">
            FRAUD • CYBER • VISION • VOICE • BEHAVIOR • RECOMMENDATIONS
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Initialize session state
    if "omni_messages" not in st.session_state:
        st.session_state.omni_messages = []
    if "omni_session_id" not in st.session_state:
        st.session_state.omni_session_id = str(uuid.uuid4())
    if "omni_attached_image" not in st.session_state:
        st.session_state.omni_attached_image = None
    if "omni_attached_audio" not in st.session_state:
        st.session_state.omni_attached_audio = None
    if "omni_attached_video" not in st.session_state:
        st.session_state.omni_attached_video = None
    if "omni_image_name" not in st.session_state:
        st.session_state.omni_image_name = None
    if "omni_audio_name" not in st.session_state:
        st.session_state.omni_audio_name = None
    if "omni_video_name" not in st.session_state:
        st.session_state.omni_video_name = None

    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("### ⚙️ Settings")

        use_rag = st.toggle("📚 Enable RAG", value=True, help="Use Retrieval-Augmented Generation")
        enable_vision = st.toggle("👁️ Vision Analysis", value=True, help="Analyze images and videos")
        enable_voice = st.toggle("🎤 Voice Emotion", value=True, help="Analyze audio emotion")
        enable_risk = st.toggle("🛡️ Risk Detection", value=True, help="Fraud/Cyber/Behavior scoring")
        enable_recommendations = st.toggle(
            "🎯 Recommendations", value=True, help="Movie/Product suggestions"
        )

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("### 📊 Statistics")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f"""
            <div class="metric-card">
                <div class="metric-value">{len(st.session_state.omni_messages)}</div>
                <div class="metric-label">Messages</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col2:
            user_msgs = sum(1 for m in st.session_state.omni_messages if m.get("role") == "user")
            st.markdown(
                f"""
            <div class="metric-card">
                <div class="metric-value">{user_msgs}</div>
                <div class="metric-label">Queries</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("### 🎨 Features")

        features = [
            ("💳", "Fraud Detection"),
            ("🔐", "Cyber Threat Analysis"),
            ("🎭", "Behavior Profiling"),
            ("📸", "Image Recognition"),
            ("🎥", "Video Analysis"),
            ("🗣️", "Voice Emotion AI"),
            ("🎬", "Movie Recommendations"),
            ("🛍️", "Product Discovery"),
            ("📚", "Document Q&A"),
            ("🤖", "AI Agent Chat"),
        ]

        for icon, feature in features:
            st.markdown(f"{icon} {feature}")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("### 🗑️ Actions")

        col1, col2 = st.columns(2)
        with col1:
            if call_with_container_width(st.button, "🗑️ Clear Chat", key="omni_clear_chat"):
                st.session_state.omni_messages = []
                st.session_state.omni_attached_image = None
                st.session_state.omni_attached_audio = None
                st.session_state.omni_attached_video = None
                st.rerun()

        with col2:
            if call_with_container_width(st.button, "🔄 New Session", key="omni_new_session"):
                st.session_state.omni_session_id = str(uuid.uuid4())
                st.session_state.omni_messages = []
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown(f"**Session ID:** `{st.session_state.omni_session_id[:8]}...`")
        st.markdown(f"**Time:** {datetime.now().strftime('%H:%M:%S')}")
        st.markdown("</div>", unsafe_allow_html=True)

    # Main chat area
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    # Display messages
    if not st.session_state.omni_messages:
        st.markdown(
            """
        <div style="text-align: center; padding: 60px 20px; color: #94a3b8;">
            <div style="font-size: 64px; margin-bottom: 20px;">👋</div>
            <h2 style="color: #e2e8f0; margin-bottom: 12px;">Welcome to Sentinel!</h2>
            <p style="font-size: 16px; line-height: 1.6;">
                I'm your comprehensive AI assistant powered by advanced machine learning models.<br>
                Ask me anything about fraud detection, cybersecurity, image analysis, voice emotion,<br>
                or get personalized recommendations!
            </p>
            <div style="margin-top: 30px;">
                <span class="status-badge info">🚀 All Systems Online</span>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        for idx, msg in enumerate(st.session_state.omni_messages):
            role = msg.get("role", "user")
            content = msg.get("content", "")

            # Sanitize content to prevent XSS
            safe_content = html.escape(content)

            if role == "user":
                safe_badges = [html.escape(badge) for badge in msg.get("badges", [])]
                st.markdown(
                    f"""
                <div class="message-row user">
                    <div class="message-content">
                        <strong style="color: #fbbf24;">👤 You</strong>
                        <div style="margin-top: 6px;">{safe_content}</div>
                        {"".join([f'<span class="attachment-badge">{badge}</span>' for badge in safe_badges])}
                    </div>
                    <div class="message-avatar user">👤</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                <div class="message-row assistant">
                    <div class="message-avatar assistant">🤖</div>
                    <div class="message-content">
                        <strong style="color: #60a5fa;">🤖 Sentinel</strong>
                        <div style="margin-top: 6px;">{safe_content}</div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

    st.markdown("</div>", unsafe_allow_html=True)

    # Spacer
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)

    # Bottom input section
    st.markdown("---")

    # Media attachments section
    with st.expander("📎 Attach Media", expanded=False):
        media_tabs = st.tabs(["📷 Camera/Image", "🎤 Audio/Voice", "🎥 Video"])

        with media_tabs[0]:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**📸 Take Photo**")
                camera_input = st.camera_input(
                    "Capture", key="omni_camera", label_visibility="collapsed"
                )
                if camera_input:
                    photo_bytes = camera_input.getvalue()
                    if len(photo_bytes) > MAX_IMAGE_SIZE:
                        st.error(f"❌ Photo too large! Max: {MAX_IMAGE_SIZE/(1024*1024):.0f}MB")
                    else:
                        st.session_state.omni_attached_image = photo_bytes
                        st.session_state.omni_image_name = "camera_photo.jpg"
                        st.success("✅ Photo captured!")

            with col2:
                st.markdown("**🖼️ Upload Image**")
                uploaded_image = st.file_uploader(
                    "Upload",
                    type=["png", "jpg", "jpeg", "webp"],
                    key="omni_img_upload",
                    label_visibility="collapsed",
                )
                if uploaded_image:
                    img_bytes = uploaded_image.getvalue()
                    if len(img_bytes) > MAX_IMAGE_SIZE:
                        st.error(f"❌ Image too large! Max: {MAX_IMAGE_SIZE/(1024*1024):.0f}MB")
                    else:
                        st.session_state.omni_attached_image = img_bytes
                        st.session_state.omni_image_name = uploaded_image.name
                        st.success(f"✅ {uploaded_image.name} uploaded!")

        with media_tabs[1]:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**🎙️ Record Audio**")
                audio_recorder = st.audio_input(
                    "Record", key="omni_mic", label_visibility="collapsed"
                )
                if audio_recorder:
                    audio_bytes = audio_recorder.read()
                    if len(audio_bytes) > MAX_AUDIO_SIZE:
                        st.error(f"❌ Audio too large! Max: {MAX_AUDIO_SIZE/(1024*1024):.0f}MB")
                    else:
                        st.session_state.omni_attached_audio = audio_bytes
                        st.session_state.omni_audio_name = "recording.wav"
                        st.success("✅ Audio recorded!")

            with col2:
                st.markdown("**🎵 Upload Audio**")
                uploaded_audio = st.file_uploader(
                    "Upload",
                    type=["wav", "mp3", "m4a", "ogg", "aac"],
                    key="omni_audio_upload",
                    label_visibility="collapsed",
                )
                if uploaded_audio:
                    audio_bytes = uploaded_audio.getvalue()
                    if len(audio_bytes) > MAX_AUDIO_SIZE:
                        st.error(f"❌ Audio too large! Max: {MAX_AUDIO_SIZE/(1024*1024):.0f}MB")
                    else:
                        st.session_state.omni_attached_audio = audio_bytes
                        st.session_state.omni_audio_name = uploaded_audio.name
                        st.success(f"✅ {uploaded_audio.name} uploaded!")

        with media_tabs[2]:
            st.markdown("**🎬 Upload Video**")
            uploaded_video = st.file_uploader(
                "Upload video",
                type=["mp4", "mov", "avi", "mkv"],
                key="omni_video_upload",
                label_visibility="collapsed",
            )
            if uploaded_video:
                video_bytes = uploaded_video.getvalue()
                if len(video_bytes) > MAX_VIDEO_SIZE:
                    st.error(f"❌ Video too large! Max: {MAX_VIDEO_SIZE/(1024*1024):.0f}MB")
                else:
                    st.session_state.omni_attached_video = video_bytes
                    st.session_state.omni_video_name = uploaded_video.name
                    st.success(f"✅ {uploaded_video.name} uploaded!")

    # Show current attachments
    if any(
        [
            st.session_state.omni_attached_image,
            st.session_state.omni_attached_audio,
            st.session_state.omni_attached_video,
        ]
    ):
        st.markdown("#### 📌 Current Attachments")

        attach_cols = st.columns([2, 2, 2, 1])

        with attach_cols[0]:
            if st.session_state.omni_attached_image:
                st.image(
                    st.session_state.omni_attached_image,
                    width=150,
                    caption=st.session_state.omni_image_name,
                )

        with attach_cols[1]:
            if st.session_state.omni_attached_audio:
                st.audio(st.session_state.omni_attached_audio)
                st.caption(st.session_state.omni_audio_name)

        with attach_cols[2]:
            if st.session_state.omni_attached_video:
                st.video(st.session_state.omni_attached_video)
                st.caption(st.session_state.omni_video_name)

        with attach_cols[3]:
            if call_with_container_width(st.button, "🗑️ Clear All"):
                st.session_state.omni_attached_image = None
                st.session_state.omni_attached_audio = None
                st.session_state.omni_attached_video = None
                st.rerun()

    # Chat input
    st.markdown("#### 💬 Your Message")

    input_col1, input_col2 = st.columns([6, 1])

    with input_col1:
        prompt = st.chat_input(
            "Type your message here... Ask about fraud, cyber threats, vision analysis, or get recommendations!",
            key="omni_chat_input",
        )

    with input_col2:
        send_button = call_with_container_width(st.button, "📤 Send", type="primary")

    # Process message
    if prompt or send_button:
        if not prompt:
            st.warning("⚠️ Please type a message first!")
            st.stop()

        user_text = prompt.strip()

        # Validate message
        if not user_text:
            st.warning("⚠️ Please enter a non-empty message!")
            st.stop()

        if len(user_text) > MAX_MESSAGE_LENGTH:
            st.error(f"❌ Message too long! Maximum {MAX_MESSAGE_LENGTH} characters.")
            st.stop()

        # Remove potentially harmful characters
        user_text = user_text.replace("\0", "")  # Null bytes

        # Build badges for attachments
        badges = []
        if st.session_state.omni_attached_image:
            badges.append("📷 Image")
        if st.session_state.omni_attached_audio:
            badges.append("🎤 Audio")
        if st.session_state.omni_attached_video:
            badges.append("🎥 Video")

        # Add user message
        user_msg = {
            "role": "user",
            "content": user_text,
            "badges": badges,
            "timestamp": datetime.now().isoformat(),
        }
        st.session_state.omni_messages.append(user_msg)

        # Show typing indicator
        with st.spinner(""):
            st.markdown(
                """
            <div class="message-row assistant">
                <div class="message-avatar assistant">🤖</div>
                <div class="message-content">
                    <div class="typing-indicator">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Prepare API call
            files: dict = {}
            has_media = False

            if st.session_state.omni_attached_image:
                files["image"] = (
                    st.session_state.omni_image_name or "image.jpg",
                    st.session_state.omni_attached_image,
                    "image/jpeg",
                )
                has_media = True

            if st.session_state.omni_attached_audio:
                files["audio"] = (
                    st.session_state.omni_audio_name or "audio.wav",
                    st.session_state.omni_attached_audio,
                    "audio/wav",
                )
                has_media = True

            if st.session_state.omni_attached_video:
                files["video"] = (
                    st.session_state.omni_video_name or "video.mp4",
                    st.session_state.omni_attached_video,
                    "video/mp4",
                )
                has_media = True

            # Make API call
            try:
                if has_media:
                    # Multimodal endpoint
                    res = call_multipart(
                        "/api/chat/multimodal",
                        data={
                            "message": user_text,
                            "user_id": st.session_state.omni_session_id,
                            "use_rag": "true" if use_rag else "false",
                            "transcribe_audio": "true" if enable_voice else "false",
                            "analyze_video": "true" if enable_vision else "false",
                        },
                        files=files,
                        timeout=120.0,
                    )
                else:
                    # Text-only endpoint
                    res = call_model(
                        "/api/chat",
                        {
                            "message": user_text,
                            "user_id": st.session_state.omni_session_id,
                            "use_rag": use_rag,
                        },
                    )

                # Process response
                if isinstance(res, dict) and "error" not in res:
                    reply = res.get("reply") or res.get("answer") or res.get("response", "")

                    meta = res.get("meta") if isinstance(res.get("meta"), dict) else {}
                    meta_attachments = (
                        meta.get("attachments") if isinstance(meta.get("attachments"), dict) else {}
                    )

                    # Add analysis results if available
                    analysis_parts = []

                    if enable_risk:
                        # Fraud detection
                        if res.get("fraud_score") is not None:
                            score = res["fraud_score"]
                            risk_level = (
                                "🔴 HIGH"
                                if score > 0.7
                                else "🟡 MEDIUM" if score > 0.4 else "🟢 LOW"
                            )
                            analysis_parts.append(f"**Fraud Risk:** {risk_level} ({score:.2%})")

                        # Cyber threat
                        if res.get("cyber_score") is not None:
                            score = res["cyber_score"]
                            risk_level = (
                                "🔴 HIGH"
                                if score > 0.7
                                else "🟡 MEDIUM" if score > 0.4 else "🟢 LOW"
                            )
                            analysis_parts.append(f"**Cyber Threat:** {risk_level} ({score:.2%})")

                        # Behavior anomaly
                        if res.get("behavior_score") is not None:
                            score = res["behavior_score"]
                            status = "⚠️ ANOMALOUS" if score > 0.6 else "✅ NORMAL"
                            analysis_parts.append(f"**Behavior:** {status} ({score:.2%})")

                    if enable_voice:
                        # Check multiple possible emotion field names and nested structures
                        emotion = None
                        confidence = 0

                        # Check top-level
                        if res.get("emotion"):
                            emotion = res.get("emotion")
                            confidence = res.get("emotion_confidence") or res.get("confidence") or 0

                        # Check in meta/attachments (multimodal response)
                        elif meta_attachments.get("voice"):
                            voice = meta_attachments["voice"]
                            emotion = voice.get("emotion")
                            confidence = voice.get("confidence") or 0

                        # Legacy locations (older responses)
                        elif res.get("meta", {}).get("voice"):
                            voice = res["meta"]["voice"]
                            emotion = voice.get("emotion")
                            confidence = voice.get("confidence") or 0

                        # Check attachments directly
                        elif res.get("attachments", {}).get("voice"):
                            voice = res["attachments"]["voice"]
                            emotion = voice.get("emotion")
                            confidence = voice.get("confidence") or 0

                        if emotion:
                            # Capitalize emotion and add emoji
                            emotion_emoji = {
                                "happy": "😊",
                                "sad": "😢",
                                "angry": "😠",
                                "fear": "😨",
                                "neutral": "😐",
                                "surprise": "😲",
                                "disgust": "🤢",
                                "calm": "😌",
                                "excited": "🤩",
                                "anxious": "😰",
                            }
                            emoji = emotion_emoji.get(emotion.lower(), "🎭")
                            emotion_display = (
                                emotion.capitalize() if isinstance(emotion, str) else emotion
                            )
                            conf_display = (
                                f"{confidence:.1%}"
                                if isinstance(confidence, (int, float))
                                else "N/A"
                            )
                            analysis_parts.append(
                                f"**Voice Emotion:** {emoji} {emotion_display} ({conf_display} confidence)"
                            )

                        # Also check for audio transcription
                        transcript = None
                        if res.get("transcription"):
                            transcript = res.get("transcription")
                        elif meta_attachments.get("stt", {}).get("text"):
                            transcript = meta_attachments["stt"]["text"]
                        elif res.get("meta", {}).get("stt", {}).get("text"):
                            transcript = res["meta"]["stt"]["text"]
                        elif res.get("attachments", {}).get("stt", {}).get("text"):
                            transcript = res["attachments"]["stt"]["text"]

                        if transcript:
                            analysis_parts.append(f'**Transcription:** "{transcript}"')

                    if enable_vision:
                        # Check for vision label/classification in various locations
                        vision_label = None
                        vision_conf = 0

                        # Check top-level
                        if res.get("vision_label"):
                            vision_label = res.get("vision_label")
                            vision_conf = res.get("vision_confidence") or 0
                        elif res.get("label"):
                            vision_label = res.get("label")
                            vision_conf = res.get("confidence") or 0

                        # Check in meta/attachments (multimodal response)
                        elif meta_attachments.get("vision_image"):
                            vision = meta_attachments["vision_image"]
                            vision_label = vision.get("label")
                            vision_conf = vision.get("confidence") or 0

                        # Legacy locations (older responses)
                        elif res.get("meta", {}).get("vision_image"):
                            vision = res["meta"]["vision_image"]
                            vision_label = vision.get("label")
                            vision_conf = vision.get("confidence") or 0
                        elif res.get("attachments", {}).get("vision_image"):
                            vision = res["attachments"]["vision_image"]
                            vision_label = vision.get("label")
                            vision_conf = vision.get("confidence") or 0

                        if vision_label:
                            conf_display = (
                                f"{vision_conf:.1%}"
                                if isinstance(vision_conf, (int, float))
                                else "N/A"
                            )
                            analysis_parts.append(
                                f"**Vision Classification:** 🔍 {vision_label} ({conf_display})"
                            )

                        # Face emotion (image-based, optional)
                        face_emotion = None
                        if meta_attachments.get("face_emotion"):
                            face_emotion = meta_attachments.get("face_emotion")
                        elif res.get("meta", {}).get("face_emotion"):
                            face_emotion = res.get("meta", {}).get("face_emotion")
                        elif res.get("attachments", {}).get("face_emotion"):
                            face_emotion = res.get("attachments", {}).get("face_emotion")

                        if isinstance(face_emotion, dict) and face_emotion.get("emotion"):
                            emo = face_emotion.get("emotion")
                            conf = face_emotion.get("confidence") or 0
                            conf_display = (
                                f"{conf:.1%}" if isinstance(conf, (int, float)) else "N/A"
                            )
                            analysis_parts.append(f"**Face Emotion:** 😊 {emo} ({conf_display})")

                        # Check for detected objects
                        objects = (
                            res.get("objects_detected")
                            or res.get("objects")
                            or res.get("detections")
                        )
                        if objects and isinstance(objects, list):
                            obj_list = ", ".join([str(obj) for obj in objects[:10]])  # Limit to 10
                            analysis_parts.append(f"**Objects Detected:** 🎯 {obj_list}")

                        # Check for video analysis
                        video_label = None
                        if meta_attachments.get("vision_video"):
                            video = meta_attachments.get("vision_video")
                            video_label = video.get("label") if isinstance(video, dict) else None
                        elif res.get("meta", {}).get("vision_video"):
                            video = res["meta"]["vision_video"]
                            video_label = video.get("label")
                        elif res.get("attachments", {}).get("vision_video"):
                            video = res["attachments"]["vision_video"]
                            video_label = video.get("label")

                        if video_label:
                            analysis_parts.append(f"**Video Analysis:** 🎬 {video_label}")

                        # Check for scene description
                        if res.get("scene_description") or res.get("description"):
                            desc = res.get("scene_description") or res.get("description")
                            analysis_parts.append(f"**Scene:** 🖼️ {desc}")

                    if enable_recommendations and res.get("recommendations"):
                        recs = res["recommendations"]
                        if isinstance(recs, list) and recs:
                            rec_text = "\n\n**🎯 Recommendations:**\n"
                            for i, rec in enumerate(recs[:5], 1):
                                title = rec.get("title") or rec.get("name", "Item")
                                rec_text += f"{i}. {title}\n"
                            analysis_parts.append(rec_text)

                    # Combine reply with analysis
                    if analysis_parts:
                        reply += "\n\n" + "\n\n".join(analysis_parts)

                    if not reply:
                        reply = "✅ I've processed your request successfully!"

                    # Add debug info in expander (only in development)
                    if os.getenv("DEBUG_MODE") == "true":
                        reply += "\n\n---\n**Debug Info:**"
                        reply += f"\n```json\n{str(res)[:500]}\n```"

                else:
                    error_msg = (
                        res.get("error", "Unknown error") if isinstance(res, dict) else str(res)
                    )
                    reply = f"❌ **Error:** {error_msg}"

            except requests.ConnectionError as e:
                reply = "❌ **Connection Error:** Cannot reach the backend server. Please ensure the API is running."
                logger.error(f"Backend connection failed: {e}")
            except requests.Timeout as e:
                reply = "⏱️ **Timeout:** The request took too long. Try with smaller files or simpler queries."
                logger.warning(f"Request timeout: {e}")
            except requests.HTTPError as e:
                status_code = e.response.status_code
                if status_code == 413:
                    reply = "❌ **File Too Large:** Your upload exceeds the server's maximum size limit."
                elif status_code == 500:
                    reply = "❌ **Server Error:** The backend encountered an internal error. Please try again later."
                elif status_code == 404:
                    reply = "❌ **Not Found:** The requested endpoint doesn't exist. Check your backend URL."
                else:
                    reply = f"❌ **HTTP Error {status_code}:** {e.response.text[:200]}"
                logger.error(f"HTTP error {status_code}: {e}", exc_info=True)
            except ValueError as e:
                reply = "❌ **Invalid Response:** The server returned unexpected data format."
                logger.error(f"Response parsing error: {e}", exc_info=True)
            except Exception as e:
                reply = f"❌ **Unexpected Error:** {str(e)[:200]}"
                logger.error(f"Unexpected error in chat handler: {traceback.format_exc()}")

            # Add assistant message
            assistant_msg = {
                "role": "assistant",
                "content": reply,
                "timestamp": datetime.now().isoformat(),
            }
            st.session_state.omni_messages.append(assistant_msg)

            # Clear attachments
            st.session_state.omni_attached_image = None
            st.session_state.omni_attached_audio = None
            st.session_state.omni_attached_video = None
            st.session_state.omni_image_name = None
            st.session_state.omni_audio_name = None
            st.session_state.omni_video_name = None

        st.rerun()


def main():
    """Standalone entry point for Sentifargo Unified."""
    st.set_page_config(
        page_title="Sentifargo - Unified AI Assistant",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    backend_url = (
        (
            os.environ.get("Sentifargo_BACKEND")
            or os.environ.get("OMNICHATX_BACKEND")
            or os.environ.get("OMNINEX_BACKEND")
            or "http://localhost:8000"
        )
        .strip()
        .rstrip("/")
    )

    # Health check on startup
    try:
        health_resp = requests.get(f"{backend_url}/health", timeout=5)
        if health_resp.status_code == 200:
            logger.info(f"✅ Connected to backend: {backend_url}")
        else:
            st.warning(f"⚠️ Backend returned status {health_resp.status_code}")
    except requests.ConnectionError:
        st.error(f"❌ Cannot connect to backend at {backend_url}")
        st.info("💡 Make sure the backend server is running")
        logger.error(f"Backend connection failed: {backend_url}")
    except requests.Timeout:
        st.warning("⏱️ Backend is slow to respond")
        logger.warning(f"Backend health check timeout: {backend_url}")
    except Exception as e:
        st.warning(f"⚠️ Backend health check failed: {e}")
        logger.warning(f"Backend health check error: {e}")

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

    def call_get(
        path: str, *, params: dict[str, str | int | float] | None = None, timeout: float = 15.0
    ) -> dict:
        try:
            resp = requests.get(
                f"{backend_url}{path}", params=params, headers=_auth_headers(), timeout=timeout
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            return {"error": str(exc)}

    render_unified_chat(
        backend_url=backend_url,
        call_model=call_model,
        call_multipart=call_multipart,
        call_get=call_get,
        auth_headers=_auth_headers,
    )


if __name__ == "__main__":
    main()
