"""Centralized filesystem paths for UAIS-V."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
LAKE_DIR = DATA_DIR / "lake"
PROCESSED_DIR = DATA_DIR / "processed"
SEQUENCES_DIR = DATA_DIR / "sequences"

CONFIG_DIR = PROJECT_ROOT / "configs"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

__all__ = [
    "PROJECT_ROOT",
    "DATA_DIR",
    "RAW_DIR",
    "LAKE_DIR",
    "PROCESSED_DIR",
    "SEQUENCES_DIR",
    "CONFIG_DIR",
    "NOTEBOOKS_DIR",
    "ARTIFACTS_DIR",
]
