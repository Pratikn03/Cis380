from __future__ import annotations

import logging
import re
import uuid
from typing import Callable

from PIL import Image
import streamlit as st

from streamlit_chatbot.recommender_router import route_recommendation
from streamlit_chatbot.image_tags import extract_tags_from_image

logger = logging.getLogger(__name__)


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
        return "SentinelForge knowledge sources"
    return mapping.get(intent, "SentinelForge knowledge sources")


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


def render_command_center(
    *,
    backend_url: str,
    call_model: Callable[..., dict],
    call_multipart: Callable[..., dict],
) -> None:
    """Recommendations UI (text + multimodal)."""

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    tabs = st.tabs(["Text Recommendations", "Multimodal (Image + Text)"])

    with tabs[0]:
        st.markdown("### Text Recommendations")
        st.caption("Movies • Electronics • Courses • News/Places (fallbacks if APIs are missing).")

        st.markdown("#### Style from Image (quick tags)")
        uploaded = st.file_uploader(
            "Choose an image", type=["png", "jpg", "jpeg"], key="style_image_upload"
        )
        if uploaded:
            try:
                img = Image.open(uploaded).convert("RGB")
                tags = extract_tags_from_image(img, top_k=5)
                if tags:
                    st.success(f"Detected tags: {', '.join(tags)}")
                else:
                    st.warning("No tags detected.")
            except Exception as exc:
                st.error(f"Image processing failed: {exc}")

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

        user_input = st.text_input("Ask for recommendations…", key="recs_text_input")
        if st.button("Send", key="recs_send", type="primary") and user_input.strip():
            prompt = user_input.strip()
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking…"):
                    rec = route_recommendation(prompt)
                    if rec.get("route") == "recommend":
                        items = rec.get("items") or []
                        answer = format_items(rec.get("intent") or "Recommendations", items)
                        st.caption(domain_source_label(rec.get("intent")))
                    else:
                        res = call_model("/api/chat", {"message": prompt})
                        if isinstance(res, dict) and "error" in res:
                            answer = res["error"]
                        else:
                            answer = (
                                (res or {}).get("reply") or (res or {}).get("answer") or str(res)
                            )
                    st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

    with tabs[1]:
        st.markdown("### Multimodal (Image + Text)")
        st.caption(
            "Backend: `/api/recommend/multimodal` (local multimodal; supports text-only, image-only, or both)."
        )

        mm_col1, mm_col2 = st.columns([1, 2])
        with mm_col1:
            mm_image = st.file_uploader(
                "Image (optional)",
                type=["png", "jpg", "jpeg", "webp"],
                key="multimodal_image_upload",
            )
        with mm_col2:
            mm_text = st.text_input("Text query (optional)", key="multimodal_text_query")

        mm_top_k = st.slider("Top-K", min_value=1, max_value=20, value=5, key="multimodal_top_k")
        mm_domain = st.selectbox(
            "Domain filter",
            ["All", "Movies", "Electronics", "Courses"],
            index=0,
            key="multimodal_domain",
        )
        mm_budget = st.text_input("Budget (e.g., under $800)", value="", key="multimodal_budget")

        if st.button("Run multimodal recommendation", key="multimodal_run", type="primary"):
            if not mm_text and mm_image is None:
                st.warning("Type a query or upload an image to get recommendations.")
                return
            payload: dict[str, str] = {"top_k": str(mm_top_k)}
            if mm_text and mm_text.strip():
                payload["text"] = mm_text.strip()
            files = None
            if mm_image is not None:
                files = {
                    "image": (
                        mm_image.name or "image.jpg",
                        mm_image.getvalue(),
                        mm_image.type or "image/jpeg",
                    )
                }
            res = call_multipart(
                "/api/recommend/multimodal", data=payload, files=files, timeout=90.0
            )
            if "error" in res:
                st.error(res["error"])
            elif "detail" in res and res.get("detail"):
                st.warning(str(res["detail"]))
            else:
                items = res.get("items") or []
                explanation = res.get("explanation")
                explainability = res.get("explainability") or {}
                visual = res.get("visual") or {}
                if mm_budget or mm_domain != "All":
                    constraint_labels = []
                    if mm_budget:
                        constraint_labels.append(f"Budget: {mm_budget}")
                    if mm_domain != "All":
                        constraint_labels.append(f"Domain: {mm_domain}")
                    st.caption("Constraints applied: " + " · ".join(constraint_labels))
                if explanation:
                    st.caption(f"Explanation: {explanation}")
                used = explainability.get("used")
                if used:
                    st.caption(f"Used signals: {used}")
                category = visual.get("category")
                objects = visual.get("objects")
                if category or objects:
                    bits = []
                    if category:
                        bits.append(f"category={category}")
                    if objects:
                        bits.append("objects=" + ", ".join(list(objects)[:5]))
                    st.caption("Visual context: " + " · ".join(bits))
                if items:
                    st.success("Multimodal recommendations")
                    for item in items:
                        title = item.get("title") or "Item"
                        meta_bits: list[str] = []
                        if item.get("category"):
                            meta_bits.append(item["category"])
                        if item.get("brand"):
                            meta_bits.append(f"Brand: {item['brand']}")
                        if item.get("price") is not None:
                            try:
                                meta_bits.append(f"${float(item['price']):.2f}")
                            except Exception:
                                meta_bits.append(f"Price: {item.get('price')}")
                        meta_bits.append(f"Score: {item.get('score', 0):.3f}")
                        st.markdown(f"**{title}**")
                        if meta_bits:
                            st.caption(" · ".join(meta_bits))
                        source = item.get("source") or "catalog"
                        st.markdown(
                            f"<span class='tag'>Source: {source}</span>", unsafe_allow_html=True
                        )
                        if item.get("image_path"):
                            st.code(str(item.get("image_path")), language="text")
                else:
                    st.info("No items returned. Try a different query or upload.")

        with st.expander("Raw API (debug)", expanded=False):
            txt = st.text_input("Text", value="Dell laptop under $800", key="mm_raw_text")
            top_k = st.slider("Top-K", 1, 20, 5, 1, key="mm_raw_top_k")
            if st.button("Call API", key="mm_raw_call"):
                res = call_multipart(
                    "/api/recommend/multimodal", data={"text": txt, "top_k": str(top_k)}, files=None
                )
                st.json(res)
