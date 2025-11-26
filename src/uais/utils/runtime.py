"""Runtime and inference benchmarking utilities."""
from __future__ import annotations

import time
from typing import Any, Callable, Tuple

import numpy as np


def time_block(fn: Callable, *args, **kwargs) -> Tuple[float, Any]:
    """Measure wall time of a function call."""
    start = time.perf_counter()
    out = fn(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return elapsed, out


def measure_inference(model: Any, X: Any, n_runs: int = 100) -> float:
    """Average inference time per sample (seconds)."""
    total = 0.0
    for _ in range(n_runs):
        t0 = time.perf_counter()
        _ = model.predict(X)
        total += (time.perf_counter() - t0)
    return total / n_runs


def measure_proba(model: Any, X: Any, n_runs: int = 100) -> float:
    """Average predict_proba time per sample (seconds)."""
    total = 0.0
    for _ in range(n_runs):
        t0 = time.perf_counter()
        _ = model.predict_proba(X)
        total += (time.perf_counter() - t0)
    return total / n_runs


__all__ = ["time_block", "measure_inference", "measure_proba"]
