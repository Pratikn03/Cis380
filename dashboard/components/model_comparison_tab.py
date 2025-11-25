"""Model comparison tab."""
import json
import pandas as pd
import streamlit as st

from uais.utils.paths import EXPERIMENTS_DIR


def _gather_metrics():
    rows = []
    for domain_dir in (EXPERIMENTS_DIR).glob("*"):
        if not domain_dir.is_dir():
            continue
        metrics_dir = domain_dir / "metrics"
        for file in metrics_dir.glob("*.json"):
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
            rows.append({"domain": domain_dir.name, **data})
    return pd.DataFrame(rows)


def render_model_comparison():
    st.subheader("Model comparison")
    df = _gather_metrics()
    if df.empty:
        st.info("No metrics to compare yet.")
        return
    st.dataframe(df)


__all__ = ["render_model_comparison"]
