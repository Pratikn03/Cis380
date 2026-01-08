import io
import math
from pathlib import Path

import joblib
import numpy as np
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi import File, UploadFile
from pydantic import BaseModel

from ..deps import require_auth
from app.utils.uploads import CSV_EXTENSIONS, MAX_CSV_BYTES, read_upload_bytes, validate_upload

router = APIRouter(prefix="/api/behavior", tags=["behavior"], dependencies=[Depends(require_auth)])


class BehaviorRequest(BaseModel):
    features: list[float]


_beh_path = Path("models") / "behavior" / "behavior_lof.pkl"
_behavior = None
_behavior_error: str | None = None
_scaler = None
_lof = None


def _load_behavior():
    global _behavior, _behavior_error, _scaler, _lof

    if _behavior is not None:
        return
    if not _beh_path.exists():
        return
    if _behavior_error is not None:
        return

    try:
        _behavior = joblib.load(_beh_path)
    except Exception as exc:  # pragma: no cover - depends on local env
        _behavior_error = str(exc)
        return

    if isinstance(_behavior, dict):
        _scaler = _behavior.get("preprocessor")
        _lof = _behavior.get("model")


@router.post("")
def predict_behavior(req: BehaviorRequest):
    _load_behavior()
    if _scaler is None or _lof is None:
        detail = "Behavior model not found."
        if _beh_path.exists() and _behavior_error:
            detail = f"Behavior model failed to load: {_behavior_error}"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )
    try:
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
        )


def _first_column(df, candidates: list[str]) -> str | None:
    cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols:
            return cols[cand.lower()]
    return None


def _compute_log_features(df) -> tuple[list[str], list[float], dict[str, float]]:
    """Compute a small, stable numeric feature vector from an arbitrary log CSV."""
    n_rows = int(len(df))

    time_col = _first_column(df, ["date", "timestamp", "time", "datetime"])
    duration_sec = 0.0
    events_per_min = float(n_rows)
    if time_col:
        try:
            ts = np.array(
                np.asarray(
                    __import__("pandas")
                    .to_datetime(df[time_col], errors="coerce")
                    .dropna()
                    .astype("int64"),
                    dtype=np.int64,
                )
            )
            if ts.size >= 2:
                duration_sec = float((ts.max() - ts.min()) / 1_000_000_000)
                if duration_sec > 0:
                    events_per_min = float(n_rows) / (duration_sec / 60.0)
        except Exception:
            duration_sec = 0.0
            events_per_min = float(n_rows)

    host_col = _first_column(df, ["pc", "computer", "device", "host", "src", "src_pc", "src_host"])
    dest_col = _first_column(
        df, ["dst", "dest", "dst_pc", "dst_host", "to", "target", "recipient", "server"]
    )
    url_col = _first_column(df, ["url", "uri", "domain", "website"])
    action_col = _first_column(
        df, ["action", "event", "operation", "activity", "type", "protocol", "method"]
    )

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
        try:
            values: set[str] = set()
            for c in ip_cols:
                values.update({str(v) for v in df[c].dropna().unique().tolist()})
            unique_ip = float(len(values))
        except Exception:
            unique_ip = 0.0

    num_df = df.select_dtypes(include=[np.number])
    num_numeric_cols = float(num_df.shape[1])
    numeric_mean = 0.0
    numeric_std = 0.0
    if num_df.shape[1] > 0:
        try:
            arr = num_df.to_numpy(dtype=float).ravel()
            arr = arr[np.isfinite(arr)]
            if arr.size:
                numeric_mean = float(np.mean(arr))
                numeric_std = float(np.std(arr))
        except Exception:
            numeric_mean = 0.0
            numeric_std = 0.0

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
        float(nunique(host_col)),
        float(nunique(dest_col)),
        float(unique_ip),
        float(nunique(url_col)),
        float(nunique(action_col)),
        float(num_numeric_cols),
        float(numeric_mean),
        float(numeric_std),
        float(missing_frac),
    ]
    feature_dict = {k: float(v) for k, v in zip(feature_names, values)}
    return feature_names, values, feature_dict


@router.post("/logs")
async def predict_behavior_logs(
    file: UploadFile = File(...),
    max_rows: int = 50_000,
    top_n: int = 10,
):
    """Upload a behavior log CSV and return per-user anomaly scores (best-effort)."""
    _load_behavior()
    if _scaler is None or _lof is None:
        detail = "Behavior model not found."
        if _beh_path.exists() and _behavior_error:
            detail = f"Behavior model failed to load: {_behavior_error}"
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

    validate_upload(
        file,
        allowed_exts=CSV_EXTENSIONS,
        allowed_mimes=None,
        max_bytes=MAX_CSV_BYTES,
        kind="csv",
    )
    try:
        raw = await read_upload_bytes(file, max_bytes=MAX_CSV_BYTES, kind="csv")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not read upload: {exc}"
        ) from exc

    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover - optional in minimal envs
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Missing pandas: {exc}"
        ) from exc

    try:
        df = pd.read_csv(io.BytesIO(raw), nrows=int(max_rows) if max_rows else None)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not parse CSV: {exc}"
        ) from exc

    user_col = _first_column(df, ["user", "user_id", "userid", "employee", "employee_id"])
    groups = [(None, df)]
    if user_col:
        try:
            groups = list(df.groupby(user_col, dropna=True))
        except Exception:
            groups = [(None, df)]

    expected = int(getattr(_scaler, "n_features_in_", 0) or 0)
    schema, schema_values, _ = _compute_log_features(df.head(1))
    provided = len(schema_values)

    results: list[dict[str, object]] = []
    for user_id, g in groups:
        feature_names, feats, feature_dict = _compute_log_features(g)
        X = np.array(feats, dtype=float).reshape(1, -1)
        if expected:
            if X.shape[1] < expected:
                pad = np.zeros((1, expected - X.shape[1]), dtype=float)
                X = np.concatenate([X, pad], axis=1)
            elif X.shape[1] > expected:
                X = X[:, :expected]
        try:
            Xs = _scaler.transform(X)
            raw_score = float(_lof.decision_function(Xs)[0])
            # sigmoid(-raw_score) with overflow guard
            if raw_score >= 50:
                anomaly = 0.0
            elif raw_score <= -50:
                anomaly = 1.0
            else:
                anomaly = float(1.0 / (1.0 + math.exp(raw_score)))
        except Exception:
            raw_score = 0.0
            anomaly = 0.0
        results.append(
            {
                "user_id": None if user_id is None else str(user_id),
                "rows": int(len(g)),
                "lof_score": round(raw_score, 6),
                "anomaly_score": round(anomaly, 6),
                "features": {k: round(float(v), 6) for k, v in feature_dict.items()},
            }
        )

    results_sorted = sorted(results, key=lambda x: float(x.get("anomaly_score", 0.0)), reverse=True)
    summary = {
        "users_scored": len(results_sorted),
        "rows_read": int(len(df)),
        "feature_schema": schema,
        "model_expected_features": expected or None,
        "feature_mismatch": (
            {"provided": provided, "expected": expected}
            if expected and expected != provided
            else None
        ),
        "note": "Best-effort CSV → fixed numeric features → LOF score. For best accuracy, retrain the behavior model on the same feature_schema.",
    }

    return {
        "filename": file.filename,
        "summary": summary,
        "top_anomalous": results_sorted[: max(1, int(top_n))],
    }
