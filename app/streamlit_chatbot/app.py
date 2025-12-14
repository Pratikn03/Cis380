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

for path in (APP_ROOT, REPO_ROOT):
    p = str(path)
    if p not in sys.path:
        sys.path.append(p)

from app.chatbot.context_manager import ContextManager
from recommender_router import route_recommendation
from app.agent.orchestrator import OmniChatXOrchestrator
from image_tags import extract_tags_from_image


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
        msg = risk_orchestrator._fraud_score(f"{price} {rating} {popularity}")
        return msg
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
        "phones": "Electronics phone dataset",
        "laptops": "Electronics laptop dataset",
        "headphones": "Electronics headphone dataset",
        "courses": "Learning resources dataset",
        "clothes": "Clothes handler",
    }
    return mapping.get(intent, "OmniNex knowledge sources")


def main():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    backend_url = os.environ.get("OMNINEX_BACKEND", "http://localhost:8000")

    def call_model(path: str, payload: dict) -> dict:
        try:
            resp = requests.post(f"{backend_url}{path}", json=payload, timeout=10.0)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            return {"error": f"{exc}"}

    tabs = st.tabs(["Chat & Recommendations", "Risk & Anomaly"])

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
