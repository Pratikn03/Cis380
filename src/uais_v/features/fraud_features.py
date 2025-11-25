"""Wrappers around existing UAIS fraud feature builders."""
try:
    from uais.features.fraud_features import build_fraud_features as _core_build
except Exception:  # pragma: no cover - optional dependency
    _core_build = None


def build_fraud_features(df):  # pragma: no cover - passthrough
    if _core_build is None:
        raise ImportError("uais.features.fraud_features is not available.")
    return _core_build(df)


__all__ = ["build_fraud_features"]
