"""UAIS-V Streamlit Chatbot for Recommendations."""
from __future__ import annotations

import json
import os

import sys
from pathlib import Path

from PIL import Image
import streamlit as st

# Ensure package import works when launched via streamlit run
THIS_DIR = Path(__file__).resolve().parent
PARENT = THIS_DIR.parent
if str(PARENT) not in sys.path:
    sys.path.append(str(PARENT))

from recommender_router import route_recommendation
from image_tags import extract_tags_from_image


st.set_page_config(page_title="UAIS-V Recommender Chatbot", page_icon="🤖", layout="wide")

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


def main():
    if "messages" not in st.session_state:
        st.session_state.messages = []

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

    # Manual input box + send button (more reliable than chat_input)
    user_input = st.text_input("Ask for movies, places, or news (health/crime)...", key="manual_query")
    send = st.button("Send", type="primary")

    if send and user_input.strip():
        text = user_input.strip()
        st.session_state.messages.append({"role": "user", "content": text})
        with st.chat_message("user"):
            st.markdown(text)

        try:
            query = text
            if image_tags_text:
                query = f\"{text} {image_tags_text}\"
            rec = route_recommendation(query)
            reply = format_items(rec["category"], rec["items"])
        except Exception as exc:
            reply = f"Error: {exc}"

        with st.chat_message("assistant"):
            st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    main()
