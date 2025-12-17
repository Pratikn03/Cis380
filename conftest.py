"""Pytest configuration.

This repo uses a src-layout (see `pyproject.toml`). When tests run without
installing the package (e.g., `pytest` directly), the `src/` directory might not
be on `sys.path`, causing imports like `import uais_v` to fail.

We add `src/` to `sys.path` to make tests runnable in that mode.
"""

from __future__ import annotations

import sys
from pathlib import Path


def pytest_configure() -> None:
    repo_root = Path(__file__).resolve().parent
    src_dir = repo_root / "src"
    if src_dir.exists():
        sys.path.insert(0, str(src_dir))
