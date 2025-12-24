"""Interactive Streamlit dashboard for UAIS-V results."""

from pathlib import Path
import subprocess


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


def launch_preview(
    project_root: str | Path | None = None, *, start_server: bool = False, port: int = 8501
):
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
    st.set_page_config(page_title="UAIS-V Metrics", layout="wide")

    # Reuse the canonical Metrics page from the main Streamlit Command Center.
    from app.streamlit_chatbot.pages.metrics import render_metrics_page

    render_metrics_page()


if __name__ == "__main__":  # pragma: no cover
    if _missing:
        raise ImportError(_deps_message())
    _render_app()
