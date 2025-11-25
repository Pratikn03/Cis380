"""Overview tab components."""
import json
from pathlib import Path
import streamlit as st

from uais.utils.paths import EXPERIMENTS_DIR


def _load_summary():
    summary_path = EXPERIMENTS_DIR / "report_summary.json"
    if summary_path.exists():
        with open(summary_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def render_overview():
    st.header("Universal Anomaly Intelligence System")
    st.write("Multidomain anomaly detection playground: fraud, cyber, and behavior.")

    summary = _load_summary()
    if not summary:
        st.info("Run an experiment script to populate metrics.")
        return

    cols = st.columns(3)
    for idx, domain in enumerate(["fraud", "cyber", "behavior"]):
        with cols[idx % 3]:
            metrics = summary.get(domain, {})
            headline = next(iter(metrics.values()), {}) if metrics else {}
            st.metric(label=f"{domain.title()} F1", value=f"{headline.get('test_f1', 0):.3f}" if headline else "N/A")
            st.metric(label=f"{domain.title()} ROC-AUC", value=f"{headline.get('test_roc_auc', 0):.3f}" if headline else "N/A")


__all__ = ["render_overview"]
