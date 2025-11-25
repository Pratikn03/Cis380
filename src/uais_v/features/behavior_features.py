"""Wrappers around existing UAIS behavior feature builders."""
try:
    from uais.features.behavior_features import build_behavior_feature_table as _core_build
except Exception:  # pragma: no cover - optional dependency
    _core_build = None


def build_behavior_feature_table(df):  # pragma: no cover - passthrough
    if _core_build is None:
        raise ImportError("uais.features.behavior_features is not available.")
    return _core_build(df)


__all__ = ["build_behavior_feature_table"]
