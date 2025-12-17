from __future__ import annotations

import streamlit as st

from streamlit_chatbot.risk_dashboard import render_risk_command_center


def render_risk_page() -> None:
    # Wrapped so the router is consistent.
    render_risk_command_center()
