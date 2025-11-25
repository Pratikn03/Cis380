"""Interactive Streamlit dashboard for UAIS-V results."""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="UAIS-V Dashboard", layout="wide")
st.title("Universal Anomaly Intelligence System – Dashboard")

project_root = Path(__file__).resolve().parents[1]
experiments_dir = project_root / "experiments"
models_dir = project_root / "models"

option = st.sidebar.selectbox("Select domain", ("Fraud", "Cyber", "Behavior", "Fusion"))


def show_metrics_csv(path: Path, title: str):
    if path.exists():
        df = pd.read_csv(path)
        st.subheader(title)
        st.dataframe(df)
        if {"Metric", "Value"}.issubset(df.columns):
            fig = px.bar(df, x="Metric", y="Value", title=title)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"Metrics file not found: {path}")


def show_scores(path: Path, title: str, color: str | None = None):
    if not path.exists():
        st.warning(f"Scores file not found: {path}")
        return
    df = pd.read_csv(path)
    st.subheader(title)
    st.dataframe(df.head())
    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if len(num_cols) >= 2:
        x_col, y_col = num_cols[0], num_cols[1]
        fig = px.scatter(df, x=x_col, y=y_col, color=color if color in df.columns else None)
        st.plotly_chart(fig, use_container_width=True)


if option == "Fraud":
    show_metrics_csv(experiments_dir / "fraud" / "metrics" / "metrics.csv", "Fraud Detection Metrics")
    shap_path = experiments_dir / "fraud" / "plots" / "shap_summary.png"
    if shap_path.exists():
        st.image(str(shap_path), caption="Fraud SHAP Summary")

elif option == "Cyber":
    show_metrics_csv(experiments_dir / "cyber" / "metrics" / "metrics.csv", "Cyber Intrusion Metrics")
    shap_path = experiments_dir / "cyber" / "plots" / "shap_summary.png"
    if shap_path.exists():
        st.image(str(shap_path), caption="Cyber SHAP Summary")

elif option == "Behavior":
    st.subheader("Behavior Anomaly Insights")
    plot_path = experiments_dir / "behavior" / "plots" / "heatmap.png"
    if plot_path.exists():
        st.image(str(plot_path))
    sal_path = experiments_dir / "behavior" / "plots" / "saliency.csv"
    if sal_path.exists():
        st.dataframe(pd.read_csv(sal_path))
    if not plot_path.exists() and not sal_path.exists():
        st.info("Add plots to experiments/behavior/plots/heatmap.png or saliency.csv")

elif option == "Fusion":
    scores_path = experiments_dir / "fusion" / "fusion_scores.csv"
    show_scores(scores_path, "Fusion Scores", color="label")
    # Vision Grad-CAM preview if available
    gradcam_path = experiments_dir / "vision" / "plots" / "gradcam.png"
    if gradcam_path.exists():
        st.image(str(gradcam_path), caption="Vision Grad-CAM")

st.sidebar.markdown("### Model Artifacts")
st.sidebar.write({
    "fraud_model": (models_dir / "fraud" / "supervised" / "fraud_model.pkl").exists(),
    "cyber_model": (models_dir / "cyber" / "supervised" / "cyber_model.pkl").exists(),
    "fusion_model": (experiments_dir / "fusion" / "models" / "fusion_meta_model.pkl").exists(),
})
