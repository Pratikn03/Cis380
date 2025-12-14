"""Train the behavior anomaly models and write standard artifacts.

This script is a stable entrypoint intended for demos/CI:
- Trains an autoencoder + LOF on behavior features
- Saves to `models/behavior/behavior_autoencoder.pkl` and `models/behavior/behavior_lof.pkl`
"""

from __future__ import annotations

import subprocess
import sys


def main() -> None:
    subprocess.run([sys.executable, "src/scripts/run_behavior_experiment.py"], check=True)


if __name__ == "__main__":
    main()
