"""Sequence building utilities."""
from typing import List, Tuple

import numpy as np
import pandas as pd


def build_sequences(
    df: pd.DataFrame,
    id_column: str,
    time_column: str,
    target_column: str,
) -> Tuple[List[np.ndarray], List[int]]:
    """Group events by id and sort by time to produce variable-length sequences."""
    sequences: List[np.ndarray] = []
    labels: List[int] = []

    df = df.sort_values(time_column)
    feature_cols = [c for c in df.columns if c not in {id_column, time_column, target_column}]

    for _, group in df.groupby(id_column):
        labels.append(int(group[target_column].max()))
        sequences.append(group[feature_cols].to_numpy())
    return sequences, labels


def pad_sequences(sequences: List[np.ndarray], max_len: int | None = None) -> Tuple[np.ndarray, np.ndarray]:
    if not sequences:
        return np.array([]), np.array([])
    feature_dim = sequences[0].shape[1]
    max_len = max_len or max(seq.shape[0] for seq in sequences)
    padded = np.zeros((len(sequences), max_len, feature_dim))
    mask = np.zeros((len(sequences), max_len))
    for i, seq in enumerate(sequences):
        length = min(seq.shape[0], max_len)
        padded[i, :length, :] = seq[:length]
        mask[i, :length] = 1
    return padded, mask


__all__ = ["build_sequences", "pad_sequences"]
