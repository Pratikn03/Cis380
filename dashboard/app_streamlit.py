"""Interactive Streamlit dashboard for UAIS-V results."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="UAIS-V Dashboard", layout="wide")
st.title("Universal Anomaly Intelligence System – Dashboard")

project_root = Path(__file__).resolve().parents[1]
experiments_dir = project_root / "experiments"

option = st.sidebar.selectbox("Select domain", ("Fraud", "Cyber", "Behavior", "Fusion"))

if option == "Fraud":
    metrics_path = experiments_dir / "fraud" / "metrics" / "metrics.csv"
    if metrics_path.exists():
        df = pd.read_csv(metrics_path)
        st.subheader("Fraud Detection Metrics")
        st.dataframe(df)
        fig = px.bar(df, x="Metric", y="Value", title="Fraud Model Performance")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Fraud metrics file not found.")

elif option == "Cyber":
    metrics_path = experiments_dir / "cyber" / "metrics" / "metrics.csv"
    if metrics_path.exists():
        df = pd.read_csv(metrics_path)
        st.subheader("Cyber Model Metrics")
        st.line_chart(df.set_index("Metric"))
    else:
        st.warning("Cyber metrics file not found.")

elif option == "Behavior":
    st.subheader("Behavior Anomaly Insights")
    plot_path = experiments_dir / "behavior" / "plots" / "heatmap.png"
    if plot_path.exists():
        st.image(str(plot_path))
    else:
        st.info("Add plots to experiments/behavior/plots/heatmap.png")

elif option == "Fusion":
    scores_path = experiments_dir / "fusion" / "fusion_scores.csv"
    if scores_path.exists():
        df = pd.read_csv(scores_path)
        st.subheader("Fusion Meta-Model Output")
        st.dataframe(df.head())
        if {"fraud_score", "fusion_score", "label"}.issubset(df.columns):
            fig = px.scatter(df, x="fraud_score", y="fusion_score", color="label")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Fusion scores file not found.")

st.success("Dashboard ready. Switch domains via sidebar.")
