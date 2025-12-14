"""Train the cyber supervised model and write standard artifacts.

This script is a stable entrypoint intended for demos/CI:
- Trains a supervised cyber model
- Saves to `models/cyber/supervised/cyber_model.pkl`
"""

from __future__ import annotations

import subprocess
import sys


def main() -> None:
    subprocess.run([sys.executable, "src/scripts/run_cyber_experiment.py"], check=True)


if __name__ == "__main__":
    main()
