from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

try:  # Optional charting
    import plotly.express as px
except Exception:  # pragma: no cover
    px = None


REPO_ROOT = Path(__file__).resolve().parents[3]
EXPERIMENTS_DIR = REPO_ROOT / "experiments"
MODELS_DIR = REPO_ROOT / "models"
ARTIFACTS_DIR = REPO_ROOT / "artifacts"

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
TABLE_EXTS = {".csv"}
TEXT_EXTS = {".txt", ".md", ".json"}


def _load_metrics(domain: str) -> pd.DataFrame | None:
    metrics_path = EXPERIMENTS_DIR / domain / "metrics" / "metrics.csv"
    if not metrics_path.exists():
        return None
    df = pd.read_csv(metrics_path)
    if {"Metric", "Value"}.issubset(df.columns):
        df = df.assign(Domain=domain.title())
    return df


def _describe_file(path: Path) -> str:
    try:
        stat = path.stat()
        size_mb = stat.st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        return f"{size_mb:.2f} MB • {mtime}"
    except Exception:
        return ""


def _render_model_status() -> None:
    st.markdown("### 🧠 Model Artifacts")

    checks: list[tuple[str, Path]] = [
        ("Fraud (supervised)", MODELS_DIR / "fraud" / "supervised" / "fraud_model.pkl"),
        ("Cyber (supervised)", MODELS_DIR / "cyber" / "supervised" / "cyber_model.pkl"),
        ("Behavior (LOF)", MODELS_DIR / "behavior" / "behavior_lof.pkl"),
        ("Fusion", MODELS_DIR / "fusion" / "fusion_meta_model.pkl"),
        ("Voice emotion", MODELS_DIR / "voice_emotion.pkl"),
        ("Vision (ResNet)", MODELS_DIR / "vision" / "resnet" / "model.pt"),
        ("Face emotion (image)", MODELS_DIR / "vision" / "face_emotion" / "model.pt"),
        ("Vision (video temporal)", MODELS_DIR / "vision" / "video_temporal_model.pkl"),
        ("Brand YOLO", ARTIFACTS_DIR / "brand" / "yolo_logo_det.pt"),
        ("Recommender", MODELS_DIR / "recommender" / "recommender_model.pkl"),
        ("NLP intent", MODELS_DIR / "nlp" / "intent_classifier.pkl"),
    ]

    cols = st.columns(2)
    for idx, (name, path) in enumerate(checks):
        col = cols[idx % 2]
        with col:
            if path.exists():
                st.success(f"✅ {name}")
            else:
                st.warning(f"⏳ {name}")
            meta = _describe_file(path) if path.exists() else ""
            st.caption(f"`{path}`" + (f" • {meta}" if meta else ""))


def _render_experiments() -> None:
    st.markdown("### 📊 Experiment Metrics")
    st.caption("Reads from `experiments/<domain>/metrics/metrics.csv` when available.")

    if not EXPERIMENTS_DIR.exists():
        st.info("No `experiments/` directory found. Run training/experiment scripts to generate metrics.")
        return

    option = st.selectbox(
        "Domain",
        ("All domains", "Fraud", "Cyber", "Behavior", "Vision", "Fusion"),
        key="metrics_domain",
    )

    domains = {
        "Fraud": "fraud",
        "Cyber": "cyber",
        "Behavior": "behavior",
        "Vision": "vision",
        "Fusion": "fusion",
    }

    if option == "All domains":
        frames: list[pd.DataFrame] = []
        missing: list[str] = []
        for dom in domains.values():
            df = _load_metrics(dom)
            if df is None:
                missing.append(dom)
                continue
            frames.append(df)
        if not frames:
            st.info("No metrics found yet. Expected: `experiments/<domain>/metrics/metrics.csv`.")
            return
        combined = pd.concat(frames, ignore_index=True)
        pivot = combined.pivot_table(index="Metric", columns="Domain", values="Value")
        st.dataframe(pivot, use_container_width=True)
        if px is not None:
            fig = px.bar(combined, x="Metric", y="Value", color="Domain", barmode="group")
            st.plotly_chart(fig, use_container_width=True)
        if missing:
            st.caption(f"Missing: {', '.join(missing)}")
        return

    dom = domains.get(option)
    if not dom:
        return
    df = _load_metrics(dom)
    if df is None:
        st.info(f"No metrics file found for `{dom}`.")
        return
    st.dataframe(df, use_container_width=True)
    if px is not None and {"Metric", "Value"}.issubset(df.columns):
        fig = px.bar(df, x="Metric", y="Value", title=f"{option} metrics")
        st.plotly_chart(fig, use_container_width=True)


def _collect_artifacts(domain: str) -> list[Path]:
    base = EXPERIMENTS_DIR / domain
    if not base.exists():
        return []
    paths: list[Path] = []
    for sub in ("explainability", "plots"):
        dir_path = base / sub
        if not dir_path.exists():
            continue
        for p in sorted(dir_path.glob("*")):
            if p.is_file():
                paths.append(p)
    return paths


def _render_explainability() -> None:
    st.markdown("### 🧾 Explainability & Plots")
    st.caption("Previews files from `experiments/<domain>/{plots,explainability}` when available.")

    if not EXPERIMENTS_DIR.exists():
        st.info("No `experiments/` directory found. Run training/experiment scripts to generate artifacts.")
        return

    domain = st.selectbox("Domain", ["fraud", "cyber", "behavior", "vision", "fusion"], index=0, key="explain_domain")
    artifacts = _collect_artifacts(domain)
    if not artifacts:
        st.info(f"No artifacts found for `{domain}` yet.")
        return

    images = [p for p in artifacts if p.suffix.lower() in IMAGE_EXTS]
    tables = [p for p in artifacts if p.suffix.lower() in TABLE_EXTS]
    texts = [p for p in artifacts if p.suffix.lower() in TEXT_EXTS]

    if images:
        st.subheader("Images")
        for img in images:
            st.image(str(img), caption=f"{img.name} • {_describe_file(img)}", use_container_width=True)

    if tables:
        st.subheader("Tables")
        for tbl in tables:
            st.markdown(f"**{tbl.name}**")
            try:
                df = pd.read_csv(tbl)
                preview = df.head(200)
                st.dataframe(preview, use_container_width=True)
                if len(df) > len(preview):
                    st.caption(f"Showing first {len(preview)} of {len(df)} rows.")
            except Exception as exc:
                st.warning(f"Could not read {tbl.name}: {exc}")

    if texts:
        st.subheader("Text")
        for txt in texts:
            try:
                content = txt.read_text(encoding="utf-8")
            except Exception as exc:
                st.warning(f"Could not read {txt.name}: {exc}")
                continue
            st.markdown(f"**{txt.name}**")
            st.code(content[:4000])
            if len(content) > 4000:
                st.caption("Truncated preview.")


def render_metrics_page() -> None:
    st.markdown("## 📈 Metrics & Artifacts")
    tabs = st.tabs(["🧠 Artifacts", "📊 Metrics", "🧾 Explainability"])
    with tabs[0]:
        _render_model_status()
    with tabs[1]:
        _render_experiments()
    with tabs[2]:
        _render_explainability()
