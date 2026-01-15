from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], *, env: dict[str, str]) -> None:
    result = subprocess.run(cmd, env=env, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> int:
    ap = argparse.ArgumentParser(description="Prepare + train YOLO brand model by kind.")
    ap.add_argument("--kind", choices=["logo", "car", "fashion"], default="logo")
    ap.add_argument("--src_root", default=None, help="Raw dataset root (optional).")
    ap.add_argument("--out_root", default=None, help="Processed YOLO output root (optional).")
    ap.add_argument("--data_yaml", default=None, help="Prebuilt YOLO dataset yaml.")
    ap.add_argument("--out_path", default=None, help="Output weights path.")
    args = ap.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["BRAND_KIND"] = args.kind

    data_yaml = args.data_yaml
    if data_yaml is None:
        cmd = [sys.executable, str(project_root / "scripts" / "prepare_brand_data.py"), "--kind", args.kind]
        if args.src_root:
            cmd.extend(["--src_root", args.src_root])
        if args.out_root:
            cmd.extend(["--out_root", args.out_root])
        _run(cmd, env=env)

        out_root = Path(args.out_root or f"data/processed/brand_yolo/{args.kind}")
        data_yaml = str(project_root / out_root / "brands.yaml")

    env["BRAND_DATA_YAML"] = data_yaml
    if args.out_path:
        env["BRAND_OUT_PATH"] = args.out_path

    _run([sys.executable, "-m", "src.train.train_brand_logo_detector"], env=env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
