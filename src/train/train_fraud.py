"""Train the fraud supervised model and write standard artifacts.

This script is a stable entrypoint intended for demos/CI:
- Trains a supervised fraud model
- Saves to `models/fraud/supervised/fraud_model.pkl`
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    src_path = str(project_root / "src")
    current_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{src_path}{os.pathsep}{current_pythonpath}" if current_pythonpath else src_path
    )
    cache_root = project_root / ".cache"
    mpl_cache = cache_root / "matplotlib"
    cache_root.mkdir(parents=True, exist_ok=True)
    mpl_cache.mkdir(parents=True, exist_ok=True)
    env.setdefault("XDG_CACHE_HOME", str(cache_root))
    env.setdefault("MPLCONFIGDIR", str(mpl_cache))
    subprocess.run(
        [sys.executable, "src/scripts/run_fraud_experiment.py"],
        check=True,
        cwd=str(project_root),
        env=env,
    )


if __name__ == "__main__":
    main()
