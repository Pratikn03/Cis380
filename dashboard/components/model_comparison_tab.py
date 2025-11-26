"""Model comparison tab."""
import json
from pathlib import Path
import pandas as pd
import streamlit as st

from uais.utils.paths import EXPERIMENTS_DIR


def _load_metrics_file(file: Path) -> dict:
    if file.suffix == ".json":
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    if file.suffix == ".csv":
        try:
            df = pd.read_csv(file)
        except Exception:
            return {}
        if df.empty:
            return {}
        if {"Metric", "Value"}.issubset(df.columns):
            return dict(zip(df["Metric"], df["Value"]))
        return df.iloc[0].to_dict()
    return {}


def _gather_metrics():
    rows = []
    for domain_dir in EXPERIMENTS_DIR.glob("*"):
        if not domain_dir.is_dir():
            continue
        metrics_dir = domain_dir / "metrics"
        if not metrics_dir.exists():
            continue
        files = sorted(metrics_dir.glob("*.json")) + sorted(metrics_dir.glob("*.csv"))
        for file in files:
            data = _load_metrics_file(file)
            if not data:
                continue
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
