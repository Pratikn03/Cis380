from __future__ import annotations


def test_multimodal_recommender_import_is_lightweight():
    # Import-only test: should not trigger model downloads.
    from app.models.recommender.multimodal import image_embed, multimodal_predict  # noqa: F401

    assert hasattr(image_embed, "embed_text")
    assert hasattr(multimodal_predict, "multimodal_recommend")
