"""UAIS-V Streamlit Chatbot for Recommendations."""
from __future__ import annotations

import json
import os

import streamlit as st

from uais.recommender.recommend_actions import recommend_from_text


st.set_page_config(page_title="UAIS-V Recommender Chatbot", page_icon="🤖", layout="wide")
st.title("🤖 UAIS-V Recommender Chatbot")
st.caption("Cross-domain anomaly → action recommendations (BLOCK / REVIEW / MONITOR / ALLOW)")

# Sidebar tips
st.sidebar.header("How to use")
st.sidebar.markdown(
    """
    - Enter an event in **key=value** form or JSON (e.g., `{"amount": 5000, "type": "CASH_OUT"}`).
    - The bot will parse, score domain models, fuse risk, and recommend an action.
    - Models must exist under `models/` and `experiments/fusion/models/`.
    """
)


def format_result(result: dict) -> str:
    lines = [
        f"**Action:** {result.get('action')}",
        f"**Confidence:** {result.get('confidence', 0):.3f}",
    ]
    scores = result.get("scores", {})
    if scores:
        lines.append("**Scores:** " + ", ".join(f"{k}={v:.3f}" for k, v in scores.items()))
    expl = result.get("explanation")
    if expl:
        lines.append(f"**Explanation:** {expl}")
    return "\n\n".join(lines)


def main():
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Enter event details (key=value pairs or JSON)...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        try:
            result = recommend_from_text(user_input)
            reply = format_result(result)
        except Exception as exc:
            reply = f"Error: {exc}"

        with st.chat_message("assistant"):
            st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    main()
