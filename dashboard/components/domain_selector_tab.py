"""Domain selector tab."""
import streamlit as st


def render_domain_selector() -> str:
    st.subheader("Choose domain")
    domain = st.radio("Domain", ["fraud", "cyber", "behavior", "vision", "fusion"], horizontal=True)
    st.caption("Switch between domains to view metrics and explanations.")
    return domain


__all__ = ["render_domain_selector"]
