"""Timing context manager for quick profiling."""
import time
from contextlib import contextmanager
from typing import Iterator


@contextmanager
def timer(name: str) -> Iterator[None]:
    start = time.time()
    yield
    elapsed = time.time() - start
    print(f"[{name}] {elapsed:.2f}s")


__all__ = ["timer"]
