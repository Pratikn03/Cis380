"""Interactive Streamlit dashboard for UAIS-V results."""
from pathlib import Path
import subprocess

import pandas as pd

# Optional dependencies: Streamlit + Plotly.
_missing = []
try:  # pragma: no cover - optional UI deps
    import streamlit as st
except ImportError:  # pragma: no cover
    st = None
    _missing.append("streamlit")

try:  # pragma: no cover
    import plotly.express as px
except ImportError:  # pragma: no cover
    px = None
    _missing.append("plotly")


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS_DIR = PROJECT_ROOT / "experiments"
MODELS_DIR = PROJECT_ROOT / "models"


def _deps_message() -> str:
    return (
        f"Dashboard requires {', '.join(_missing)}. "
        "Install with `pip install streamlit plotly` to enable the preview."
    )


def launch_preview(project_root: str | Path | None = None, *, start_server: bool = False, port: int = 8501):
    """Helper for notebooks/scripts to point to the Streamlit app."""
    app_root = Path(project_root) if project_root else PROJECT_ROOT
    app_path = app_root / "dashboard" / "app_streamlit.py"
    if _missing:
        print(f"[warn] {_deps_message()} App located at: {app_path}")
        return
    cmd = ["streamlit", "run", str(app_path), "--server.headless=true", f"--server.port={port}"]
    print("[info] Dashboard app:", app_path)
    print("[hint] Launch via:", " ".join(cmd))
    if start_server:
        subprocess.Popen(cmd, cwd=app_root)
        print(f"[ok] Streamlit server starting on port {port}")


def _render_app():  # pragma: no cover - UI code
    st.set_page_config(page_title="UAIS-V Dashboard", layout="wide")
    st.title("Universal Anomaly Intelligence System – Dashboard")

    option = st.sidebar.selectbox("Select domain", ("Fraud", "Cyber", "Behavior", "Vision", "Fusion"))

    def show_metrics_csv(path: Path, title: str):
        if path.exists():
            df = pd.read_csv(path)
            st.subheader(title)
            st.dataframe(df)
            if {"Metric", "Value"}.issubset(df.columns) and px is not None:
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
        if len(num_cols) >= 2 and px is not None:
            x_col, y_col = num_cols[0], num_cols[1]
            fig = px.scatter(df, x=x_col, y=y_col, color=color if color in df.columns else None)
            st.plotly_chart(fig, use_container_width=True)

    if option == "Fraud":
        show_metrics_csv(EXPERIMENTS_DIR / "fraud" / "metrics" / "metrics.csv", "Fraud Detection Metrics")
        shap_path = EXPERIMENTS_DIR / "fraud" / "plots" / "shap_summary.png"
        if shap_path.exists():
            st.image(str(shap_path), caption="Fraud SHAP Summary")

    elif option == "Cyber":
        show_metrics_csv(EXPERIMENTS_DIR / "cyber" / "metrics" / "metrics.csv", "Cyber Intrusion Metrics")
        shap_path = EXPERIMENTS_DIR / "cyber" / "plots" / "shap_summary.png"
        if shap_path.exists():
            st.image(str(shap_path), caption="Cyber SHAP Summary")

    elif option == "Behavior":
        st.subheader("Behavior Anomaly Insights")
        plot_path = EXPERIMENTS_DIR / "behavior" / "plots" / "heatmap.png"
        if plot_path.exists():
            st.image(str(plot_path))
        sal_path = EXPERIMENTS_DIR / "behavior" / "plots" / "saliency.csv"
        if sal_path.exists():
            st.dataframe(pd.read_csv(sal_path))
        if not plot_path.exists() and not sal_path.exists():
            st.info("Add plots to experiments/behavior/plots/heatmap.png or saliency.csv")

    elif option == "Vision":
        show_metrics_csv(EXPERIMENTS_DIR / "vision" / "metrics" / "metrics.csv", "Vision Forgery Metrics")
        show_scores(EXPERIMENTS_DIR / "vision" / "scores.csv", "Vision Scores", color="label")
        gradcam_path = EXPERIMENTS_DIR / "vision" / "plots" / "gradcam.png"
        if gradcam_path.exists():
            st.image(str(gradcam_path), caption="Vision Grad-CAM")
        else:
            st.info("Add Grad-CAM image to experiments/vision/plots/gradcam.png to preview.")

    elif option == "Fusion":
        scores_path = EXPERIMENTS_DIR / "fusion" / "fusion_scores.csv"
        show_scores(scores_path, "Fusion Scores", color="label")
        # Vision Grad-CAM preview if available
        gradcam_path = EXPERIMENTS_DIR / "vision" / "plots" / "gradcam.png"
        if gradcam_path.exists():
            st.image(str(gradcam_path), caption="Vision Grad-CAM")

    st.sidebar.markdown("### Model Artifacts")
    st.sidebar.write(
        {
            "fraud_model": (MODELS_DIR / "fraud" / "supervised" / "fraud_model.pkl").exists(),
            "cyber_model": (MODELS_DIR / "cyber" / "supervised" / "cyber_model.pkl").exists(),
            "fusion_model": (EXPERIMENTS_DIR / "fusion" / "models" / "fusion_meta_model.pkl").exists(),
        }
    )


if __name__ == "__main__":  # pragma: no cover
    if _missing:
        raise ImportError(_deps_message())
    _render_app()
