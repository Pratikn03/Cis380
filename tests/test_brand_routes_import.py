def test_brand_route_import_does_not_require_weights():
    """Importing the route should not try to load YOLO weights (lazy-load on request)."""
    import app.api.brand  # noqa: F401
