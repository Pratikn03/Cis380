from __future__ import annotations


def test_unified_catalog_loads_multiple_domains():
    from app.models.recommender.multimodal.catalog import load_unified_catalog

    catalog = load_unified_catalog()
    # Should have at least movies + courses + some electronics.
    assert isinstance(catalog, dict)
    assert len(catalog) > 100

    # Spot check presence of domain keys
    has_movie = any(k.startswith("catalog://movies/") for k in catalog)
    has_course = any(k.startswith("catalog://courses/") for k in catalog)
    has_elec = any(
        k.startswith("catalog://phones/")
        or k.startswith("catalog://laptops/")
        or k.startswith("catalog://headphones/")
        for k in catalog
    )
    assert has_movie
    assert has_course
    assert has_elec
