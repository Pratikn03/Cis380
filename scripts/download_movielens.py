"""
Download MovieLens 20M via Kaggle API and place ratings under data/raw/recommendation/movielens.csv.

Prereqs:
- kaggle installed (`pip install kaggle`)
- Kaggle API token at ~/.kaggle/kaggle.json (or set KAGGLE_USERNAME/KAGGLE_KEY env vars)
"""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

import kaggle  # type: ignore

DATA_DIR = Path("data/raw/recommendation")
DEST_FILE = DATA_DIR / "movielens.csv"
TMP_DIR = Path("tmp_movielens_download")
ARCHIVE_DIR = Path("data/raw/archive")


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = TMP_DIR / "movielens-20m-dataset.zip"

    print("Downloading MovieLens 20M via Kaggle API...")
    kaggle.api.dataset_download_files(
        "grouplens/movielens-20m-dataset", path=str(TMP_DIR), quiet=False, unzip=False
    )

    if not zip_path.exists():
        # try to find the zip if named differently
        zips = list(TMP_DIR.glob("*.zip"))
        if not zips:
            raise FileNotFoundError("Downloaded zip not found in tmp directory.")
        zip_path = zips[0]

    print(f"Unzipping {zip_path}...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(TMP_DIR)

    # Locate rating file
    rating_path = None
    for candidate in ["rating.csv", "ratings.csv"]:
        p = TMP_DIR / candidate
        if p.exists():
            rating_path = p
            break
    if rating_path is None:
        # search within subfolders
        for p in TMP_DIR.rglob("rating*.csv"):
            rating_path = p
            break
    if rating_path is None:
        raise FileNotFoundError("Could not find rating.csv in extracted files.")

    print(f"Copying {rating_path} -> {DEST_FILE}")
    shutil.copyfile(rating_path, DEST_FILE)
    print(f"Done. Ratings stored at {DEST_FILE}")

    # Optionally move full archive files into data/raw/archive for reuse
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    for fname in ["movie.csv", "link.csv", "tag.csv", "genome_scores.csv", "genome_tags.csv"]:
        src = TMP_DIR / fname
        if src.exists():
            shutil.copyfile(src, ARCHIVE_DIR / fname)

    # Clean up tmp
    shutil.rmtree(TMP_DIR, ignore_errors=True)


if __name__ == "__main__":
    main()
