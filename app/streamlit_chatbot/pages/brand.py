from __future__ import annotations

from typing import Callable

import streamlit as st


def render_brand_page(*, call_upload: Callable[..., dict]) -> None:
    st.markdown("## Brand Recognition")
    st.caption("Logo detection via `/api/vision/brand/predict`.")

    brand_img = st.file_uploader(
        "Upload an image",
        type=["png", "jpg", "jpeg", "webp"],
        key="brand_recognition_upload_page",
    )
    conf = st.slider(
        "Confidence threshold",
        min_value=0.05,
        max_value=0.95,
        value=0.25,
        step=0.05,
        key="brand_conf_page",
    )

    if brand_img is None:
        st.info("Upload an image to detect logos.")
        return

    st.image(brand_img, caption=brand_img.name, use_container_width=True)
    if st.button("Detect logos", key="brand_detect_page", type="primary"):
        result = call_upload(
            f"/api/vision/brand/predict?conf={conf}",
            filename=brand_img.name or "image.jpg",
            content=brand_img.getvalue(),
            content_type=brand_img.type or "image/jpeg",
        )
        if "error" in result:
            st.error(result["error"])
        else:
            st.success(f"Detections: {len(result.get('detections') or [])}")
            st.json(result)
