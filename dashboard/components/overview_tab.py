"""Overview tab components."""
import json
from pathlib import Path
import pandas as pd
import streamlit as st

from uais.utils.paths import EXPERIMENTS_DIR


def _load_summary():
    summary_path = EXPERIMENTS_DIR / "report_summary.json"
    if summary_path.exists():
        with open(summary_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _load_fallback_metrics():
    """Read headline metrics from per-domain metrics.csv files."""
    summary = {}
    for domain in ["fraud", "cyber", "behavior", "vision", "fusion"]:
        metrics_path = EXPERIMENTS_DIR / domain / "metrics" / "metrics.csv"
        if not metrics_path.exists():
            continue
        try:
            df = pd.read_csv(metrics_path)
        except Exception:
            continue
        if df.empty:
            continue
        if {"Metric", "Value"}.issubset(df.columns):
            metrics = dict(zip(df["Metric"], df["Value"]))
        else:
            metrics = df.iloc[0].to_dict()
        summary[domain] = {
            "test_f1": metrics.get("f1") or metrics.get("test_f1"),
            "test_roc_auc": metrics.get("roc_auc") or metrics.get("test_roc_auc"),
        }
    return summary


def render_overview():
    st.header("Universal Anomaly Intelligence System")
    st.write("Multidomain anomaly detection playground: fraud, cyber, behavior, vision, and fusion.")

    summary = _load_summary()
    if not summary:
        summary = _load_fallback_metrics()
    if not summary:
        st.info("Run an experiment script to populate metrics.")
        return

    domains = [d for d in ["fraud", "cyber", "behavior", "vision", "fusion"] if summary.get(d)]
    if not domains:
        st.info("No metrics found across domains.")
        return

    cols = st.columns(3)
    for idx, domain in enumerate(domains):
        metrics = summary.get(domain, {})
        f1 = metrics.get("test_f1") or metrics.get("f1")
        roc_auc = metrics.get("test_roc_auc") or metrics.get("roc_auc")
        with cols[idx % 3]:
            st.metric(label=f"{domain.title()} F1", value=f"{f1:.3f}" if isinstance(f1, (int, float)) else "N/A")
            st.metric(label=f"{domain.title()} ROC-AUC", value=f"{roc_auc:.3f}" if isinstance(roc_auc, (int, float)) else "N/A")


__all__ = ["render_overview"]
