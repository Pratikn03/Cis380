"""Explainability tab."""
from pathlib import Path

import pandas as pd
import streamlit as st

from uais.utils.paths import EXPERIMENTS_DIR

IMAGE_EXTS = {".png", ".jpg", ".jpeg"}
TEXT_EXTS = {".txt", ".md", ".json"}
TABLE_EXTS = {".csv"}


def _collect_artifacts(domain: str) -> list[Path]:
    base = EXPERIMENTS_DIR / domain
    paths = []
    for sub in ("explainability", "plots"):
        dir_path = base / sub
        if not dir_path.exists():
            continue
        for p in sorted(dir_path.glob("*")):
            if p.is_file():
                paths.append(p)
    return paths


def _render_tables(tables: list[Path]):
    for tbl in tables:
        st.markdown(f"**{tbl.name}**")
        try:
            df = pd.read_csv(tbl)
            preview = df.head(200)
            st.dataframe(preview)
            if len(df) > len(preview):
                st.caption(f"Showing first {len(preview)} of {len(df)} rows.")
        except Exception as exc:
            st.warning(f"Could not read {tbl.name}: {exc}")


def _render_texts(texts: list[Path]):
    for txt in texts:
        try:
            content = txt.read_text()
        except Exception as exc:
            st.warning(f"Could not read {txt.name}: {exc}")
            continue
        st.markdown(f"**{txt.name}**")
        st.code(content[:4000])
        if len(content) > 4000:
            st.caption(f"Truncated preview of {txt.name}")


def _render_images(images: list[Path]):
    for img in images:
        st.image(str(img), caption=img.name, use_column_width=True)


def render_explainability(domain: str):
    st.subheader(f"Explainability: {domain.title()}")
    artifacts = _collect_artifacts(domain)
    if not artifacts:
        st.info(
            "No explainability artifacts found yet. Run the domain flow to generate SHAP/LIME/Grad-CAM or saliency outputs."
        )
        return

    images = [p for p in artifacts if p.suffix.lower() in IMAGE_EXTS]
    tables = [p for p in artifacts if p.suffix.lower() in TABLE_EXTS]
    texts = [p for p in artifacts if p.suffix.lower() in TEXT_EXTS]

    if images:
        _render_images(images)
    if tables:
        _render_tables(tables)
    if texts:
        _render_texts(texts)
    if not any((images, tables, texts)):
        st.write("Artifacts found but not previewable; see files under experiments for details.")


__all__ = ["render_explainability"]
