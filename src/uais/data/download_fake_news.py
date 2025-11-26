"""Download Fake and Real News dataset via kagglehub (optional).

Usage:
    python -m src.uais.data.download_fake_news

Requires:
    pip install kagglehub
    Kaggle credentials configured (if required by kagglehub)
"""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
TARGET_DIR = PROJECT_ROOT / "data" / "raw" / "nlp" / "fakenews"


def download_fake_news() -> Path:
    try:
        import kagglehub
    except ImportError as exc:  # pragma: no cover
        raise ImportError("kagglehub not installed. Run: pip install kagglehub") from exc

    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    print("[info] Downloading Fake and Real News dataset via kagglehub...")
    src_path = Path(kagglehub.dataset_download("clmentbisaillon/fake-and-real-news-dataset"))
    print(f"[info] kagglehub downloaded to: {src_path}")

    # If kagglehub returns a zip file, extract; otherwise copy contents
    if src_path.suffix == ".zip":
        with zipfile.ZipFile(src_path, "r") as zf:
            zf.extractall(TARGET_DIR)
        print(f"[ok] Extracted zip to {TARGET_DIR}")
    else:
        # copy tree if not already inside target
        if src_path.is_dir():
            for item in src_path.iterdir():
                dest = TARGET_DIR / item.name
                if item.is_dir():
                    if not dest.exists():
                        shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
        else:
            raise FileNotFoundError(f"Unexpected download artifact: {src_path}")
        print(f"[ok] Copied dataset to {TARGET_DIR}")

    return TARGET_DIR


def main():  # pragma: no cover
    try:
        out = download_fake_news()
        print("Dataset ready at", out)
    except Exception as exc:
        print("[error] Fake news download failed:", exc)


if __name__ == "__main__":
    main()
