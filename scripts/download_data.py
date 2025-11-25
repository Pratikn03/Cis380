"""Download helper for NLP (Enron) and Vision (CIFAR-10) datasets.

- Enron emails via Kaggle API (or manual CSV check)
- CIFAR-10 from official URL

Usage:
    python scripts/download_data.py --all
    python scripts/download_data.py --enron --no-kaggle
"""
import argparse
import tarfile
from pathlib import Path

import requests

# Optional Kaggle support
try:  # pragma: no cover - optional dependency
    from kaggle.api.kaggle_api_extended import KaggleApi

    KAGGLE_AVAILABLE = True
except ImportError:  # pragma: no cover
    KAGGLE_AVAILABLE = False

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
NLP_DIR = DATA_RAW / "nlp"
VISION_DIR = DATA_RAW / "vision"
CIFAR10_URL = "https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz"


def makedirs():
    NLP_DIR.mkdir(parents=True, exist_ok=True)
    VISION_DIR.mkdir(parents=True, exist_ok=True)


def download_file(url: str, dest_path: Path, chunk_size: int = 1 << 20):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists():
        print(f"[skip] {dest_path} already exists")
        return dest_path

    print(f"[download] {url}")
    resp = requests.get(url, stream=True)
    resp.raise_for_status()

    total = int(resp.headers.get("content-length", 0))
    downloaded = 0

    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=chunk_size):
            if not chunk:
                continue
            f.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                pct = downloaded * 100 // total
                print(f"\r  -> {downloaded / (1 << 20):.1f} MB ({pct}%)", end="")
    print(f"\n[ok] saved to {dest_path}")
    return dest_path


# -----------
# NLP (Enron)
# -----------

def download_enron_via_kaggle() -> Path:
    if not KAGGLE_AVAILABLE:
        raise RuntimeError(
            "kaggle package not installed. Install it or use --no-kaggle for manual mode."
        )

    NLP_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = NLP_DIR / "enron_emails.csv"
    if csv_path.exists():
        print(f"[skip] {csv_path} already exists")
        return csv_path

    print("[info] Downloading Enron dataset from Kaggle via API ...")
    api = KaggleApi()
    api.authenticate()
    api.dataset_download_files("wcukierski/enron-email-dataset", path=str(NLP_DIR), quiet=False)

    import zipfile

    zip_files = list(NLP_DIR.glob("*.zip"))
    if not zip_files:
        raise FileNotFoundError("No zip found after Kaggle download.")
    zip_path = zip_files[0]
    print(f"[info] Extracting {zip_path.name} ...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(NLP_DIR)

    candidates = list(NLP_DIR.glob("*.csv"))
    if not candidates:
        raise FileNotFoundError("No CSV found in Enron zip. Check dataset contents.")
    src_csv = candidates[0]
    src_csv.rename(csv_path)
    zip_path.unlink(missing_ok=True)
    print(f"[ok] Enron CSV available at: {csv_path}")
    return csv_path


def download_enron_manual() -> Path:
    csv_path = NLP_DIR / "enron_emails.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"{csv_path} not found. Download Enron CSV manually (e.g., Kaggle) and place it there."
        )
    print(f"[ok] Found existing Enron CSV at {csv_path}")
    return csv_path


def download_enron(prefer_kaggle: bool = True) -> Path:
    makedirs()
    if prefer_kaggle:
        try:
            return download_enron_via_kaggle()
        except Exception as e:
            print("[warn] Kaggle download failed:", e)
            print("[info] Falling back to manual CSV check...")
    return download_enron_manual()


# --------------
# Vision CIFAR-10
# --------------

def download_cifar10() -> Path:
    makedirs()
    tar_path = VISION_DIR / "cifar-10-python.tar.gz"
    target_dir = VISION_DIR / "cifar-10-python"

    if target_dir.exists() and any(target_dir.iterdir()):
        print(f"[skip] {target_dir} already contains files")
        return target_dir

    download_file(CIFAR10_URL, tar_path)
    print(f"[info] Extracting {tar_path.name} ...")
    with tarfile.open(tar_path, "r:gz") as tf:
        tf.extractall(VISION_DIR)

    default_dir = VISION_DIR / "cifar-10-batches-py"
    if default_dir.exists():
        default_dir.rename(target_dir)

    print(f"[ok] CIFAR-10 extracted to: {target_dir}")
    return target_dir


# -----
# CLI
# -----

def main():
    parser = argparse.ArgumentParser(description="Download NLP (Enron) and Vision (CIFAR-10) datasets for UAIS-V.")
    parser.add_argument("--enron", action="store_true", help="Download/prepare Enron email CSV.")
    parser.add_argument("--cifar10", action="store_true", help="Download CIFAR-10 image dataset.")
    parser.add_argument("--all", action="store_true", help="Download both Enron and CIFAR-10.")
    parser.add_argument("--no-kaggle", action="store_true", help="Do NOT use Kaggle API for Enron.")
    args = parser.parse_args()

    if not (args.enron or args.cifar10 or args.all):
        parser.print_help()
        return

    prefer_kaggle = not args.no_kaggle
    if args.all or args.enron:
        print("\n=== Enron (NLP) ===")
        download_enron(prefer_kaggle=prefer_kaggle)
    if args.all or args.cifar10:
        print("\n=== CIFAR-10 (Vision) ===")
        download_cifar10()


if __name__ == "__main__":
    main()
