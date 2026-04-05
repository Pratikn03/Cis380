from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from urllib.request import urlretrieve


DEFAULT_CFG_URL = "https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3.cfg"
DEFAULT_WEIGHTS_URL = "https://pjreddie.com/media/files/yolov3.weights"
DEFAULT_NAMES_URL = "https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download YOLOv3 weights + cfg + coco names.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("artifacts/vision/yolov3"),
        help="Output directory.",
    )
    parser.add_argument("--cfg-url", type=str, default=DEFAULT_CFG_URL)
    parser.add_argument("--weights-url", type=str, default=DEFAULT_WEIGHTS_URL)
    parser.add_argument("--names-url", type=str, default=DEFAULT_NAMES_URL)
    parser.add_argument("--force", action="store_true", help="Redownload files.")
    return parser.parse_args()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path, force: bool) -> None:
    if dest.exists() and not force:
        print(f"[download] exists: {dest}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"[download] {url} -> {dest}")
    urlretrieve(url, dest)
    print(f"[download] sha256={sha256(dest)}")


def main() -> None:
    args = parse_args()
    cfg_path = args.out_dir / "yolov3.cfg"
    weights_path = args.out_dir / "yolov3.weights"
    names_path = args.out_dir / "coco.names"

    download(args.cfg_url, cfg_path, args.force)
    download(args.weights_url, weights_path, args.force)
    download(args.names_url, names_path, args.force)

    print("\n✅ YOLOv3 assets ready.")
    print(f"CFG: {cfg_path}")
    print(f"WEIGHTS: {weights_path}")
    print(f"NAMES: {names_path}")


if __name__ == "__main__":
    sys.exit(main())
