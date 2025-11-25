"""Build 30-sequence arrays from behavior data or synthetic fallback."""
from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from ..logging_utils import setup_logging
from ..paths import PROCESSED_DIR, SEQUENCES_DIR
from ..utils.seed import set_global_seed
from .load_datasets import load_behavior_events

logger = setup_logging(__name__)


@dataclass
class SequenceBuildConfig:
    seq_len: int = 30
    n_features: int = 16
    anomaly_ratio: float = 0.2
    min_events_per_entity: int = 6
    seed: int = 42


def _pad_or_truncate(x: np.ndarray, seq_len: int) -> np.ndarray:
    """Pad (pre) or truncate (tail) a 2D array to seq_len."""
    length, feat_dim = x.shape
    if length == seq_len:
        return x
    if length > seq_len:
        return x[-seq_len:]
    pad = np.zeros((seq_len - length, feat_dim), dtype=x.dtype)
    return np.vstack([pad, x])


def _coerce_feature_dim(x: np.ndarray, target_dim: int) -> np.ndarray:
    if x.shape[1] == target_dim:
        return x
    if x.shape[1] > target_dim:
        return x[:, :target_dim]
    pad = np.zeros((x.shape[0], target_dim - x.shape[1]), dtype=x.dtype)
    return np.hstack([x, pad])


def _prepare_behavior_sequences(cfg: SequenceBuildConfig) -> Tuple[Dict[str, np.ndarray], np.ndarray]:
    df = load_behavior_events()

    time_col = "date" if "date" in df.columns else "timestamp"
    if time_col not in df.columns:
        raise ValueError("Behavior data is missing a date/timestamp column.")

    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col])

    entity_col = "user" if "user" in df.columns else "id"
    if entity_col not in df.columns:
        df[entity_col] = "anon"

    df = df.sort_values([entity_col, time_col])

    df["hour"] = df[time_col].dt.hour
    df["dayofweek"] = df[time_col].dt.dayofweek
    if "filename" in df.columns:
        df["filename_len"] = df["filename"].astype(str).str.len()
    else:
        df["filename_len"] = 0
    if "content" in df.columns:
        df["content_len"] = df["content"].astype(str).str.len()
    else:
        df["content_len"] = 0
    if "pc" in df.columns:
        df["pc_code"] = df["pc"].astype("category").cat.codes
    else:
        df["pc_code"] = 0

    feature_cols = [c for c in ["hour", "dayofweek", "filename_len", "content_len", "pc_code"] if c in df.columns]
    if not feature_cols:
        raise ValueError("No numeric behavior features available to build sequences.")

    group_stats = df.groupby(entity_col)["content_len"].mean()
    threshold = group_stats.quantile(1 - cfg.anomaly_ratio) if not group_stats.empty else 0

    sequences = []
    labels = []
    for entity, group in df.groupby(entity_col):
        if len(group) < cfg.min_events_per_entity:
            continue
        feats = group[feature_cols].to_numpy(dtype=np.float32)
        feats = _coerce_feature_dim(feats, cfg.n_features)
        seq = _pad_or_truncate(feats, cfg.seq_len)
        sequences.append(seq)
        label = 1 if group["content_len"].mean() >= threshold else 0
        labels.append(label)

    if not sequences:
        raise ValueError("Behavior data available but no sequences met minimum length criterion.")

    base = np.stack(sequences).astype(np.float32)
    labels_arr = np.asarray(labels, dtype=np.int64)

    rng = np.random.default_rng(cfg.seed)
    X_dict: Dict[str, np.ndarray] = {}
    for i in range(30):
        noise_scale = 0.01 * (i + 1)
        noisy = base + rng.normal(0.0, noise_scale, base.shape)
        X_dict[f"seq_{i+1}"] = noisy.astype(np.float32)

    return X_dict, labels_arr


def _synthetic_sequences(cfg: SequenceBuildConfig, n_samples: int = 400) -> Tuple[Dict[str, np.ndarray], np.ndarray]:
    rng = np.random.default_rng(cfg.seed)
    base = rng.normal(0.0, 1.0, size=(n_samples, cfg.seq_len, cfg.n_features)).astype(np.float32)
    labels = (rng.random(n_samples) < cfg.anomaly_ratio).astype(np.int64)
    base[labels == 1] += rng.normal(1.2, 0.5, size=base[labels == 1].shape).astype(np.float32)

    X_dict: Dict[str, np.ndarray] = {}
    for i in range(30):
        jitter = rng.normal(0.0, 0.02 * (i + 1), size=base.shape).astype(np.float32)
        X_dict[f"seq_{i+1}"] = base + jitter
    return X_dict, labels


def build_30seq_arrays(cfg: SequenceBuildConfig | None = None) -> Tuple[Dict[str, np.ndarray], np.ndarray]:
    cfg = cfg or SequenceBuildConfig()
    set_global_seed(cfg.seed)

    SEQUENCES_DIR.mkdir(parents=True, exist_ok=True)

    try:
        X_dict, y = _prepare_behavior_sequences(cfg)
        logger.info("Built 30-sequence dataset from behavior data: %s sequences", len(y))
    except Exception as exc:
        logger.warning("Falling back to synthetic 30-sequence data (%s)", exc)
        X_dict, y = _synthetic_sequences(cfg)
        logger.info("Built synthetic 30-sequence dataset: %s sequences", len(y))

    np.save(SEQUENCES_DIR / "X_30seq.npy", X_dict, allow_pickle=True)
    np.save(SEQUENCES_DIR / "y_30seq.npy", y)
    return X_dict, y


def load_30seq_arrays() -> Tuple[Dict[str, np.ndarray], np.ndarray]:
    X_dict = np.load(SEQUENCES_DIR / "X_30seq.npy", allow_pickle=True).item()
    y = np.load(SEQUENCES_DIR / "y_30seq.npy")
    return X_dict, y


__all__ = ["SequenceBuildConfig", "build_30seq_arrays", "load_30seq_arrays"]
