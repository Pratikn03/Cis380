"""Explainability tab."""
import streamlit as st


def render_explainability(domain: str):
    st.subheader(f"Explainability: {domain.title()}")
    st.write("Run SHAP/LIME scripts in `uais.explainability` to populate insights.")
    st.markdown("- Use `compute_shap_importance` for tabular models.\n- Use `explain_with_lime` for per-sample narratives.\n- Sequence saliency is available via `sequence_saliency`.")


__all__ = ["render_explainability"]
