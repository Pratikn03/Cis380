"""
Auto-download datasets for the UAIS project using kagglehub.

Datasets:
1) Fraud (credit card fraud)
   - Kaggle: mlg-ulb/creditcardfraud
   - Saved to: data/raw/fraud/creditcard.csv

2) Cyber (UNSW-NB15)
   - Kaggle: mrwellsdavid/unsw-nb15
   - Saved to: data/raw/cyber/UNSW-NB15_1.csv, etc.

3) Behavior / Web sessions (Online Shoppers Intention)
   - Kaggle: mkechadi/online-shoppers-intention
   - Saved to: data/raw/behavior/online_shoppers_intention.csv
"""

from pathlib import Path
import shutil

import kagglehub  # pip install kagglehub

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "raw"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def download_creditcard_fraud() -> None:
    """Download the Kaggle credit card fraud dataset and copy creditcard.csv into data/raw/fraud/."""
    print("=== Downloading Credit Card Fraud dataset (mlg-ulb/creditcardfraud) ===")
    local_path = Path(kagglehub.dataset_download("mlg-ulb/creditcardfraud"))
    print(f"Downloaded to kagglehub cache: {local_path}")

    src_csv = local_path / "creditcard.csv"
    if not src_csv.exists():
        raise FileNotFoundError(f"creditcard.csv not found in {local_path}")

    dest_dir = DATA_DIR / "fraud"
    ensure_dir(dest_dir)
    dest_csv = dest_dir / "creditcard.csv"

    shutil.copy2(src_csv, dest_csv)
    print(f"Copied: {src_csv} -> {dest_csv}")


def download_unsw_nb15() -> None:
    """Download the UNSW-NB15 cyber intrusion dataset and copy CSV files into data/raw/cyber/."""
    print("=== Downloading UNSW-NB15 dataset (mrwellsdavid/unsw-nb15) ===")
    local_path = Path(kagglehub.dataset_download("mrwellsdavid/unsw-nb15"))
    print(f"Downloaded to kagglehub cache: {local_path}")

    dest_dir = DATA_DIR / "cyber"
    ensure_dir(dest_dir)

    csv_files = list(local_path.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {local_path}")

    for csv_file in csv_files:
        dest_csv = dest_dir / csv_file.name
        shutil.copy2(csv_file, dest_csv)
        print(f"Copied: {csv_file} -> {dest_csv}")


def download_online_shoppers_intention() -> None:
    """Download the Online Shoppers Intention dataset and copy the main CSV into data/raw/behavior/."""
    print("=== Downloading Online Shoppers Intention dataset (mkechadi/online-shoppers-intention) ===")
    local_path = Path(kagglehub.dataset_download("mkechadi/online-shoppers-intention"))
    print(f"Downloaded to kagglehub cache: {local_path}")

    dest_dir = DATA_DIR / "behavior"
    ensure_dir(dest_dir)

    csv_files = list(local_path.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {local_path}")

    src_csv = csv_files[0]
    dest_csv = dest_dir / "online_shoppers_intention.csv"

    shutil.copy2(src_csv, dest_csv)
    print(f"Copied: {src_csv} -> {dest_csv}")


def main() -> None:
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Raw data directory: {DATA_DIR}")

    ensure_dir(DATA_DIR)

    download_creditcard_fraud()
    download_unsw_nb15()
    download_online_shoppers_intention()

    print("\nAll downloads completed.")
    print("Fraud data in:   ", DATA_DIR / "fraud")
    print("Cyber data in:   ", DATA_DIR / "cyber")
    print("Behavior data in:", DATA_DIR / "behavior")


if __name__ == "__main__":
    main()
