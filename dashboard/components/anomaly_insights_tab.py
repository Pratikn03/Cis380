"""Anomaly insights tab."""
import json
from pathlib import Path
import streamlit as st

from uais.utils.paths import EXPERIMENTS_DIR


def _load_domain_metrics(domain: str):
    metrics_dir = EXPERIMENTS_DIR / domain / "metrics"
    if not metrics_dir.exists():
        return {}
    latest = sorted(metrics_dir.glob("*.json"))[-1]
    with open(latest, "r", encoding="utf-8") as f:
        return json.load(f)


def render_anomaly_insights(domain: str):
    st.subheader(f"Anomaly metrics: {domain.title()}")
    try:
        metrics = _load_domain_metrics(domain)
    except Exception:
        metrics = {}
    if not metrics:
        st.info("No metrics yet. Run an experiment script.")
        return
    cols = st.columns(3)
    metric_items = list(metrics.items())
    for idx, (name, value) in enumerate(metric_items):
        with cols[idx % 3]:
            st.metric(label=name, value=f"{value:.3f}" if isinstance(value, (int, float)) else value)


__all__ = ["render_anomaly_insights"]
