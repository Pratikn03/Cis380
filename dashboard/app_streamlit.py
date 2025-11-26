"""Interactive Streamlit dashboard for UAIS-V results."""
from pathlib import Path
import subprocess
import sys

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

# Ensure dashboard package imports work when run via Streamlit
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
src_path = PROJECT_ROOT / "src"
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = PROJECT_ROOT / "figures" / "reports"
DOMAINS = ["fraud", "cyber", "behavior", "nlp", "vision", "fusion"]


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

    # Import UI components after Streamlit is available
    from dashboard.components.overview_tab import render_overview
    from dashboard.components.model_comparison_tab import render_model_comparison
    from dashboard.components.domain_selector_tab import render_domain_selector
    from dashboard.components.anomaly_insights_tab import render_anomaly_insights
    from dashboard.components.explainability_tab import render_explainability

    option = st.sidebar.selectbox("Select view", ("All domains", "Domain detail"))

    def _standardize_metrics(df: pd.DataFrame) -> pd.DataFrame | None:
        """Best-effort conversion of arbitrary metrics CSV into Metric/Value shape."""
        if df.empty:
            return None
        if {"Metric", "Value"}.issubset(df.columns):
            return df[["Metric", "Value"]]
        # If single row of arbitrary columns, melt into Metric/Value
        if len(df) == 1:
            melted = df.iloc[0].reset_index()
            melted.columns = ["Metric", "Value"]
            return melted
        # Otherwise, try to use numeric columns and take their mean to avoid exploding rows
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if numeric_cols:
            melted = pd.DataFrame({"Metric": numeric_cols, "Value": [df[c].mean() for c in numeric_cols]})
            return melted
        return None

    def _load_domain_metrics(domain: str) -> pd.DataFrame | None:
        metrics_path = EXPERIMENTS_DIR / domain / "metrics" / "metrics.csv"
        if not metrics_path.exists():
            return None
        try:
            df = pd.read_csv(metrics_path)
        except Exception:
            return None
        df_std = _standardize_metrics(df)
        if df_std is None:
            return None
        return df_std.assign(Domain=domain.title())

    def _load_domain_scores(domain: str) -> pd.DataFrame | None:
        scores_path = (
            EXPERIMENTS_DIR / "fusion" / "fusion_scores.csv"
            if domain == "fusion"
            else EXPERIMENTS_DIR / domain / "scores.csv"
        )
        if not scores_path.exists():
            return None
        df = pd.read_csv(scores_path)
        df = df.assign(Domain=domain.title())
        return df

    def show_metrics_csv(path: Path, title: str):
        st.subheader(title)
        if not path.exists():
            st.warning(f"Metrics file not found: {path}")
            return
        try:
            df_raw = pd.read_csv(path)
        except Exception as exc:
            st.warning(f"Could not read metrics CSV: {exc}")
            return
        df = _standardize_metrics(df_raw) or df_raw
        st.dataframe(df)
        if {"Metric", "Value"}.issubset(df.columns) and px is not None:
            try:
                fig = px.bar(df, x="Metric", y="Value", title=title)
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                pass

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

    def show_runtime_metrics(domain: str):
        runtime_path = EXPERIMENTS_DIR / domain / "metrics" / "runtime.csv"
        st.subheader("Runtime metrics")
        if not runtime_path.exists():
            st.caption("No runtime.csv found yet. Run the flow to log train/predict timings.")
            return
        try:
            df = pd.read_csv(runtime_path)
        except Exception as exc:
            st.warning(f"Could not read runtime metrics: {exc}")
            return
        st.dataframe(df)
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if px is not None and numeric_cols:
            melted = df[numeric_cols].melt(var_name="Metric", value_name="Value")
            fig = px.bar(melted, x="Metric", y="Value", title="Runtime (seconds)")
            st.plotly_chart(fig, use_container_width=True)

    def show_all_scores():
        domains = DOMAINS
        stats = []
        combined_samples = []
        missing = []
        for domain in domains:
            df = _load_domain_scores(domain)
            if df is None:
                missing.append(domain)
                continue
            score_col = "fusion_score" if "fusion_score" in df.columns else ("score" if "score" in df.columns else None)
            if score_col is None:
                numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c != "label"]
                score_col = numeric_cols[0] if numeric_cols else None
            label_col = "label" if "label" in df.columns else None
            stats.append(
                {
                    "Domain": domain.title(),
                    "Rows": len(df),
                    "Score mean": f"{df[score_col].mean():.3f}" if score_col else "N/A",
                    "Score std": f"{df[score_col].std():.3f}" if score_col else "N/A",
                    "Positive rate": f"{df[label_col].mean():.3f}" if label_col else "N/A",
                }
            )
            if score_col:
                subset_cols = [score_col] + ([label_col] if label_col else [])
                sample_df = df[subset_cols].copy()
                if len(sample_df) > 500:
                    sample_df = sample_df.sample(500, random_state=42)
                sample_df = sample_df.rename(columns={score_col: "score"})
                sample_df["Domain"] = domain.title()
                combined_samples.append(sample_df)

        if not stats:
            st.info("No score files found. Place scores under experiments/<domain>/scores.csv.")
            return

        st.subheader("All-domain score stats")
        st.dataframe(pd.DataFrame(stats))

        if combined_samples and px is not None:
            combined = pd.concat(combined_samples, ignore_index=True)
            fig = px.box(combined, x="Domain", y="score", color="Domain", points="all", title="Score distribution per domain")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Sampled score distribution (up to 500 rows per domain).")
        if missing:
            st.warning(f"No score file found for: {', '.join(missing)}")

    def show_all_domain_metrics():
        domains = DOMAINS
        frames = []
        missing = []
        for domain in domains:
            df = _load_domain_metrics(domain)
            if df is None:
                missing.append(domain)
                continue
            if "Domain" not in df.columns:
                df = df.assign(Domain=domain.title())
            frames.append(df)
        if not frames:
            st.info("No metrics found. Run the experiment scripts to populate results under experiments/<domain>/metrics/metrics.csv.")
            return

        combined = pd.concat(frames, ignore_index=True)
        st.subheader("All-domain metrics")
        st.caption("Aggregated from experiments/<domain>/metrics/metrics.csv")
        pivot = combined.pivot_table(index="Metric", columns="Domain", values="Value")
        st.dataframe(pivot)
        if px is not None:
            fig = px.bar(combined, x="Metric", y="Value", color="Domain", barmode="group", title="Metrics across domains")
            st.plotly_chart(fig, use_container_width=True)
        if missing:
            st.warning(f"No metrics file found for: {', '.join(missing)}")

    def show_reports_summary():
        """Show generated summary tables/plots from reporting scripts."""
        found_any = False
        for domain in DOMAINS:
            summary_path = REPORTS_DIR / f"metrics_{domain}.csv"
            fig_path = FIGURES_DIR / f"{domain}_roc_auc.png"
            if not summary_path.exists() and not fig_path.exists():
                continue
            found_any = True
            st.subheader(f"{domain.title()} summary")
            if summary_path.exists():
                st.dataframe(pd.read_csv(summary_path))
            else:
                st.info("No summary table yet. Run `python -m src.uais.reporting.make_tables`.")
            if fig_path.exists():
                st.image(str(fig_path), caption=f"{domain.title()} ROC-AUC bar with CI")
            else:
                st.caption("Generate plots via `python -m src.uais.reporting.make_plots`.")
        if not found_any:
            st.info("No reports yet. Run the reporting scripts after flows to populate reports/ and figures/reports/.")

    def render_fusion_view():
        metrics_path = EXPERIMENTS_DIR / "fusion" / "metrics" / "metrics.csv"
        show_metrics_csv(metrics_path, "Fusion Metrics")

        scores_path = EXPERIMENTS_DIR / "fusion" / "fusion_scores.csv"
        show_scores(scores_path, "Fusion Scores", color="label")
        if scores_path.exists():
            try:
                df_scores = pd.read_csv(scores_path)
                score_cols = [c for c in df_scores.columns if c.endswith("_score") and c != "fusion_score"]
                if score_cols and "fusion_score" in df_scores.columns and px is not None:
                    corr_rows = []
                    for col in score_cols:
                        corr = df_scores[col].corr(df_scores["fusion_score"])
                        corr_rows.append({"Input": col.replace("_score", "").title(), "Correlation": corr})
                    corr_df = pd.DataFrame(corr_rows)
                    st.subheader("Fusion input alignment")
                    st.dataframe(corr_df)
                    fig = px.bar(corr_df, x="Input", y="Correlation", title="Correlation with fusion_score")
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as exc:
                st.warning(f"Fusion score analysis skipped: {exc}")

        # Vision Grad-CAM preview if available
        gradcam_path = EXPERIMENTS_DIR / "vision" / "plots" / "gradcam.png"
        if gradcam_path.exists():
            st.image(str(gradcam_path), caption="Vision Grad-CAM")

        show_runtime_metrics("fusion")

    def render_domain_view(domain: str):
        if domain == "fraud":
            show_metrics_csv(EXPERIMENTS_DIR / "fraud" / "metrics" / "metrics.csv", "Fraud Detection Metrics")
            shap_path = EXPERIMENTS_DIR / "fraud" / "plots" / "shap_summary.png"
            if shap_path.exists():
                st.image(str(shap_path), caption="Fraud SHAP Summary")
            show_runtime_metrics("fraud")

        elif domain == "cyber":
            show_metrics_csv(EXPERIMENTS_DIR / "cyber" / "metrics" / "metrics.csv", "Cyber Intrusion Metrics")
            shap_path = EXPERIMENTS_DIR / "cyber" / "plots" / "shap_summary.png"
            if shap_path.exists():
                st.image(str(shap_path), caption="Cyber SHAP Summary")
            show_runtime_metrics("cyber")

        elif domain == "behavior":
            show_metrics_csv(EXPERIMENTS_DIR / "behavior" / "metrics" / "metrics.csv", "Behavior Metrics")
            st.subheader("Behavior Anomaly Insights")
            plot_path = EXPERIMENTS_DIR / "behavior" / "plots" / "heatmap.png"
            if plot_path.exists():
                st.image(str(plot_path))
            sal_path = EXPERIMENTS_DIR / "behavior" / "plots" / "saliency.csv"
            if sal_path.exists():
                st.dataframe(pd.read_csv(sal_path))
            if not plot_path.exists() and not sal_path.exists():
                st.info("Add plots to experiments/behavior/plots/heatmap.png or saliency.csv")
            show_runtime_metrics("behavior")

        elif domain == "nlp":
            show_metrics_csv(EXPERIMENTS_DIR / "nlp" / "metrics" / "metrics.csv", "NLP Metrics")
            show_scores(EXPERIMENTS_DIR / "nlp" / "scores.csv", "NLP Scores", color="label")
            show_runtime_metrics("nlp")

        elif domain == "vision":
            show_metrics_csv(EXPERIMENTS_DIR / "vision" / "metrics" / "metrics.csv", "Vision Forgery Metrics")
            show_scores(EXPERIMENTS_DIR / "vision" / "scores.csv", "Vision Scores", color="label")
            gradcam_path = EXPERIMENTS_DIR / "vision" / "plots" / "gradcam.png"
            if gradcam_path.exists():
                st.image(str(gradcam_path), caption="Vision Grad-CAM")
            else:
                st.info("Add Grad-CAM image to experiments/vision/plots/gradcam.png to preview.")
            show_runtime_metrics("vision")

        elif domain == "fusion":
            render_fusion_view()

        render_anomaly_insights(domain)
        render_explainability(domain)

    if option == "All domains":
        tabs = st.tabs(["Overview", "Metrics", "Scores", "Reports", "Model comparison"])
        with tabs[0]:
            render_overview()
        with tabs[1]:
            show_all_domain_metrics()
        with tabs[2]:
            show_all_scores()
        with tabs[3]:
            show_reports_summary()
        with tabs[4]:
            render_model_comparison()
    else:
        domain = render_domain_selector()
        render_domain_view(domain)

    st.sidebar.markdown("### Model Artifacts")
    st.sidebar.write(
        {
            "fraud_model": (MODELS_DIR / "fraud" / "supervised" / "fraud_model.pkl").exists(),
            "cyber_model": (MODELS_DIR / "cyber" / "supervised" / "cyber_model.pkl").exists(),
            "behavior_model": (MODELS_DIR / "behavior").exists(),
            "nlp_model": (MODELS_DIR / "nlp").exists(),
            "fusion_model": (EXPERIMENTS_DIR / "fusion" / "models" / "fusion_meta_model.pkl").exists(),
            "vision_model": (MODELS_DIR / "vision" / "resnet" / "model.pt").exists(),
        }
    )


if __name__ == "__main__":  # pragma: no cover
    if _missing:
        raise ImportError(_deps_message())
    _render_app()
