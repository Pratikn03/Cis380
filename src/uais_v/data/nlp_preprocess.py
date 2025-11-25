"""Placeholder NLP preprocessing pipeline."""
from pathlib import Path
from typing import Iterable

import pandas as pd


def clean_emails(emails: Iterable[str]) -> list[str]:  # pragma: no cover - placeholder
    return [e.strip() for e in emails]


def load_enron_emails(path: Path) -> pd.DataFrame:  # pragma: no cover - placeholder
    return pd.read_csv(path)


__all__ = ["clean_emails", "load_enron_emails"]
