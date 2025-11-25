"""Wrappers around existing UAIS cyber feature builders."""
try:
    from uais.features.cyber_features import build_cyber_features as _core_build
except Exception:  # pragma: no cover - optional dependency
    _core_build = None


def build_cyber_features(df):  # pragma: no cover - passthrough
    if _core_build is None:
        raise ImportError("uais.features.cyber_features is not available.")
    return _core_build(df)


__all__ = ["build_cyber_features"]
