from __future__ import annotations

from typing import Callable

import streamlit as st


def render_tools_page(*, call_upload: Callable[..., dict]) -> None:
    st.markdown("## Tools")
    st.caption("One-off uploads for voice + vision (image + video).")

    st.markdown("### Voice Emotion Detection")
    audio_file = st.file_uploader(
        "Audio file",
        type=["wav", "mp3", "m4a", "aac", "ogg"],
        key="tools_voice_upload",
    )
    if audio_file is not None and st.button("Analyze audio", key="tools_voice_run", type="primary"):
        result = call_upload(
            "/api/voice/emotion",
            filename=audio_file.name,
            content=audio_file.getvalue(),
            content_type=audio_file.type or "audio/wav",
        )
        (st.error if "error" in result else st.json)(result)

    st.divider()

    st.markdown("### Vision (Image) Prediction")
    img = st.file_uploader(
        "Image file",
        type=["png", "jpg", "jpeg", "webp"],
        key="tools_vision_upload",
    )
    if img is not None:
        st.image(img, use_container_width=True)
        if st.button("Predict image", key="tools_vision_run", type="primary"):
            result = call_upload(
                "/api/vision/predict",
                filename=img.name,
                content=img.getvalue(),
                content_type=img.type or "image/jpeg",
            )
            (st.error if "error" in result else st.json)(result)

    st.divider()

    st.markdown("### Vision (Video) Prediction")
    vid = st.file_uploader(
        "Video file",
        type=["mp4", "mov", "avi", "mkv"],
        key="tools_video_upload",
    )
    fps = st.slider("Frame sampling FPS", 0.5, 8.0, 1.0, 0.5, key="tools_video_fps")
    max_frames = st.slider("Max frames", 5, 120, 25, 5, key="tools_video_max_frames")
    if vid is not None and st.button("Predict video", key="tools_video_run", type="primary"):
        result = call_upload(
            f"/api/vision/video/predict?fps={fps}&max_frames={max_frames}",
            filename=vid.name,
            content=vid.getvalue(),
            content_type=vid.type or "video/mp4",
        )
        (st.error if "error" in result else st.json)(result)
