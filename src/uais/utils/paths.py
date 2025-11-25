"""Centralized project paths and helpers."""
from pathlib import Path
from typing import Dict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
EXPERIMENTS_DIR = PROJECT_ROOT / "experiments"
LOGS_DIR = PROJECT_ROOT / "logs"


def ensure_directories() -> None:
    """Create common directories if they do not already exist."""
    for path in [DATA_DIR, RAW_DIR, INTERIM_DIR, PROCESSED_DIR, MODELS_DIR, EXPERIMENTS_DIR, LOGS_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def domain_paths(domain: str) -> Dict[str, Path]:
    """Return resolved paths for a given domain (fraud/cyber/behavior/fusion)."""
    ensure_directories()
    domain = domain.lower()
    return {
        "raw": RAW_DIR / domain,
        "interim": INTERIM_DIR / domain,
        "processed": PROCESSED_DIR / domain,
        "models": MODELS_DIR / domain,
        "experiments": EXPERIMENTS_DIR / domain,
    }


__all__ = [
    "PROJECT_ROOT",
    "DATA_DIR",
    "RAW_DIR",
    "INTERIM_DIR",
    "PROCESSED_DIR",
    "MODELS_DIR",
    "EXPERIMENTS_DIR",
    "LOGS_DIR",
    "ensure_directories",
    "domain_paths",
]
