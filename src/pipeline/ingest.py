"""Data ingestion utilities: raw -> lake parquet with basic validation."""
from pathlib import Path
from datetime import datetime
from typing import Optional

import pandas as pd


def _timestamp_suffix() -> str:
    return datetime.utcnow().strftime("%Y%m%d")


def ingest_csv(
    raw_path: Path,
    lake_dir: Path,
    expected_cols: Optional[list[str]] = None,
    add_ingested_at: bool = True,
) -> Path:
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw file not found: {raw_path}")

    df = pd.read_csv(raw_path)
    if expected_cols:
        missing = [c for c in expected_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Missing expected columns {missing} in {raw_path}")

    if add_ingested_at:
        df["ingested_at"] = pd.Timestamp.utcnow()

    lake_dir.mkdir(parents=True, exist_ok=True)
    out_path = lake_dir / f"{raw_path.stem}_{_timestamp_suffix()}.parquet"
    df.to_parquet(out_path, index=False)
    return out_path


def ingest_fraud(raw_dir: Path, lake_dir: Path) -> Path:
    raw_path = raw_dir / "fraud" / "creditcard.csv"
    expected = None  # creditcard.csv has many V* columns; keep flexible
    return ingest_csv(raw_path, lake_dir / "fraud", expected_cols=expected)


def ingest_cyber(raw_dir: Path, lake_dir: Path) -> Path:
    cyber_raw = raw_dir / "cyber"
    if not cyber_raw.exists():
        raise FileNotFoundError(f"Cyber raw directory not found: {cyber_raw}")
    dfs = []
    for f in sorted(cyber_raw.glob("*.csv")):
        df = pd.read_csv(f, encoding="latin1")
        dfs.append(df)
    if not dfs:
        raise FileNotFoundError(f"No cyber CSVs found in {cyber_raw}")
    df_all = pd.concat(dfs, ignore_index=True)
    df_all["ingested_at"] = pd.Timestamp.utcnow()
    out_dir = lake_dir / "cyber"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"unsw_nb15_{_timestamp_suffix()}.parquet"
    df_all.to_parquet(out_path, index=False)
    return out_path


def ingest_behavior(raw_dir: Path, lake_dir: Path) -> Path:
    raw_path = raw_dir / "behavior" / "online_shoppers_intention.csv"
    expected = ["Revenue"]
    return ingest_csv(raw_path, lake_dir / "behavior", expected_cols=expected)


def main(domain: str = "fraud"):
    project_root = Path(__file__).resolve().parents[2]
    raw_dir = project_root / "data" / "raw"
    lake_dir = project_root / "data" / "lake"
    domain = domain.lower()

    if domain == "fraud":
        out = ingest_fraud(raw_dir, lake_dir)
    elif domain == "cyber":
        out = ingest_cyber(raw_dir, lake_dir)
    elif domain in {"behavior", "behaviour"}:
        out = ingest_behavior(raw_dir, lake_dir)
    else:
        raise ValueError("domain must be fraud | cyber | behavior")

    print(f"Ingested {domain} data to {out}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest raw data into lake")
    parser.add_argument("--domain", choices=["fraud", "cyber", "behavior"], default="fraud")
    args = parser.parse_args()
    main(args.domain)
