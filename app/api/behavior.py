from __future__ import annotations

import os
import io
import math
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.utils.uploads import CSV_EXTENSIONS, MAX_CSV_BYTES, read_upload_bytes, validate_upload

router = APIRouter()


class BehaviorRequest(BaseModel):
    features: list[float]


_MODEL_PATH = Path("models") / "behavior" / "behavior_lof.pkl"
_behavior = None
_behavior_error: str | None = None
_scaler = None
_lof = None


def _use_model_backend() -> bool:
    return os.getenv("BEHAVIOR_MODEL_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _heuristic_score(features: list[float]) -> float:
    if not features:
        return 0.0
    values = [float(v) for v in features[:10]]
    mean = sum(values) / max(len(values), 1)
    variance = sum((v - mean) ** 2 for v in values) / max(len(values), 1)
    scaled = (abs(mean) * 0.6) + (variance * 0.4)
    return float(min(max(scaled / 10.0, 0.0), 1.0))


def _first_column(df, candidates: list[str]) -> str | None:
    cols = {str(c).lower(): c for c in df.columns}
    for candidate in candidates:
        if candidate.lower() in cols:
            return cols[candidate.lower()]
    return None


def _compute_log_features(df) -> tuple[list[str], list[float], dict[str, float]]:
    import numpy as np

    n_rows = int(len(df))
    time_col = _first_column(df, ["date", "timestamp", "time", "datetime"])
    duration_sec = 0.0
    events_per_min = float(n_rows)
    if time_col:
        try:
            import pandas as pd

            ts = np.asarray(
                pd.to_datetime(df[time_col], errors="coerce").dropna().astype("int64"),
                dtype=np.int64,
            )
            if ts.size >= 2:
                duration_sec = float((ts.max() - ts.min()) / 1_000_000_000)
                if duration_sec > 0:
                    events_per_min = float(n_rows) / (duration_sec / 60.0)
        except Exception:
            duration_sec = 0.0
            events_per_min = float(n_rows)

    host_col = _first_column(df, ["pc", "computer", "device", "host", "src", "src_pc"])
    dest_col = _first_column(df, ["dst", "dest", "dst_pc", "target", "server"])
    url_col = _first_column(df, ["url", "uri", "domain", "website"])
    action_col = _first_column(df, ["action", "event", "operation", "activity", "type"])

    def nunique(col: str | None) -> float:
        if not col:
            return 0.0
        try:
            return float(df[col].nunique(dropna=True))
        except Exception:
            return 0.0

    ip_cols = [c for c in df.columns if "ip" in str(c).lower()]
    unique_ip = 0.0
    if ip_cols:
        values: set[str] = set()
        for col in ip_cols:
            values.update({str(v) for v in df[col].dropna().unique().tolist()})
        unique_ip = float(len(values))

    num_df = df.select_dtypes(include=[np.number])
    numeric_mean = 0.0
    numeric_std = 0.0
    if num_df.shape[1] > 0:
        arr = num_df.to_numpy(dtype=float).ravel()
        arr = arr[np.isfinite(arr)]
        if arr.size:
            numeric_mean = float(np.mean(arr))
            numeric_std = float(np.std(arr))

    try:
        missing_frac = float(df.isna().mean().mean())
    except Exception:
        missing_frac = 0.0

    feature_names = [
        "rows",
        "duration_sec",
        "events_per_min",
        "unique_host",
        "unique_dest",
        "unique_ip",
        "unique_url",
        "unique_action",
        "num_numeric_cols",
        "numeric_mean",
        "numeric_std",
        "missing_frac",
    ]
    values = [
        float(n_rows),
        float(duration_sec),
        float(events_per_min),
        nunique(host_col),
        nunique(dest_col),
        unique_ip,
        nunique(url_col),
        nunique(action_col),
        float(num_df.shape[1]),
        numeric_mean,
        numeric_std,
        missing_frac,
    ]
    return feature_names, values, dict(zip(feature_names, values))


def _load_behavior() -> None:
    global _behavior, _behavior_error, _scaler, _lof

    if _behavior is not None:
        return
    if not _MODEL_PATH.exists():
        return
    if _behavior_error is not None:
        return

    try:
        import joblib

        _behavior = joblib.load(_MODEL_PATH)
    except Exception as exc:  # pragma: no cover - local artifact dependent
        _behavior_error = str(exc)
        return

    if isinstance(_behavior, dict):
        _scaler = _behavior.get("preprocessor")
        _lof = _behavior.get("model")


@router.post("/behavior")
def predict_behavior(req: BehaviorRequest):
    if not _use_model_backend():
        return {
            "score": _heuristic_score(req.features),
            "input_features": len(req.features),
            "expected_features": None,
        }

    _load_behavior()
    if _scaler is None or _lof is None:
        detail = "Behavior model not found."
        if _MODEL_PATH.exists() and _behavior_error:
            detail = f"Behavior model failed to load: {_behavior_error}"
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

    try:
        import numpy as np

        expected = int(getattr(_scaler, "n_features_in_", 0) or 0)
        feats = list(req.features)
        if expected:
            feats = (feats + [0.0] * expected)[:expected]
        X = np.array(feats, dtype=float).reshape(1, -1)
        Xs = _scaler.transform(X)
        score = float(_lof.decision_function(Xs)[0])

        return {
            "score": score,
            "input_features": len(req.features),
            "expected_features": expected or None,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Behavior inference failed: {exc}",
        ) from exc


@router.post("/behavior/logs")
async def predict_behavior_logs(
    file: UploadFile = File(...),
    max_rows: int = 50_000,
    top_n: int = 10,
):
    _load_behavior()
    model_available = _scaler is not None and _lof is not None
    if _use_model_backend() and not model_available:
        detail = "Behavior model not found."
        if _MODEL_PATH.exists() and _behavior_error:
            detail = f"Behavior model failed to load: {_behavior_error}"
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

    validate_upload(
        file,
        allowed_exts=CSV_EXTENSIONS,
        allowed_mimes=None,
        max_bytes=MAX_CSV_BYTES,
        kind="csv",
    )
    raw = await read_upload_bytes(file, max_bytes=MAX_CSV_BYTES, kind="csv")

    try:
        import numpy as np
        import pandas as pd
    except Exception as exc:  # pragma: no cover - optional in minimal envs
        raise HTTPException(status_code=503, detail=f"Missing pandas/numpy: {exc}") from exc

    try:
        df = pd.read_csv(io.BytesIO(raw), nrows=int(max_rows) if max_rows else None)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {exc}") from exc

    user_col = _first_column(df, ["user", "user_id", "userid", "employee", "employee_id"])
    groups = [(None, df)]
    if user_col:
        groups = list(df.groupby(user_col, dropna=True))

    expected = int(getattr(_scaler, "n_features_in_", 0) or 0) if _scaler is not None else 0
    schema, schema_values, _ = _compute_log_features(df.head(1))
    results: list[dict[str, object]] = []
    for user_id, group in groups:
        _, features, feature_dict = _compute_log_features(group)
        if model_available:
            x_data = np.array(features, dtype=float).reshape(1, -1)
            if expected:
                if x_data.shape[1] < expected:
                    pad = np.zeros((1, expected - x_data.shape[1]), dtype=float)
                    x_data = np.concatenate([x_data, pad], axis=1)
                elif x_data.shape[1] > expected:
                    x_data = x_data[:, :expected]
            try:
                scaled = _scaler.transform(x_data)
                raw_score = float(_lof.decision_function(scaled)[0])
                anomaly = (
                    0.0
                    if raw_score >= 50
                    else 1.0 if raw_score <= -50 else float(1.0 / (1.0 + math.exp(raw_score)))
                )
            except Exception:
                raw_score = 0.0
                anomaly = _heuristic_score(features)
        else:
            raw_score = 0.0
            anomaly = _heuristic_score(features)
        results.append(
            {
                "user_id": None if user_id is None else str(user_id),
                "rows": int(len(group)),
                "lof_score": round(raw_score, 6),
                "anomaly_score": round(anomaly, 6),
                "features": {k: round(float(v), 6) for k, v in feature_dict.items()},
            }
        )

    ranked = sorted(results, key=lambda item: float(item.get("anomaly_score", 0.0)), reverse=True)
    return {
        "filename": file.filename,
        "summary": {
            "users_scored": len(ranked),
            "rows_read": int(len(df)),
            "feature_schema": schema,
            "model_expected_features": expected or None,
            "feature_mismatch": (
                {"provided": len(schema_values), "expected": expected}
                if expected and expected != len(schema_values)
                else None
            ),
            "degraded": not model_available,
        },
        "top_anomalous": ranked[: max(1, int(top_n))],
    }
