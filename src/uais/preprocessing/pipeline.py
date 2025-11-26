"""Leakage-free preprocessing pipelines for tabular data."""
from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def build_tabular_pipeline(
    df: pd.DataFrame,
    target_col: str,
    scale: bool = True,
    max_cat_cardinality: int | None = None,
) -> ColumnTransformer:
    """Create a ColumnTransformer that imputes/encodes without leakage.

    Numeric: median impute + optional scaling.
    Categorical: most_frequent impute + one-hot.
    """
    feature_df = df.drop(columns=[target_col])
    # Drop columns with no observed values to avoid downstream imputer/encoder errors.
    non_empty_cols = [c for c in feature_df.columns if feature_df[c].notna().any()]
    feature_df = feature_df[non_empty_cols]
    if feature_df.shape[1] == 0:
        raise ValueError("No usable feature columns after dropping all-NA columns.")
    numeric_cols = feature_df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = feature_df.select_dtypes(exclude=[np.number]).columns.tolist()
    if max_cat_cardinality is not None and cat_cols:
        low_card = []
        for col in cat_cols:
            # Drop extremely high-cardinality identifiers (e.g., account IDs) to avoid exploding the feature space.
            n_unique = feature_df[col].nunique(dropna=True)
            if n_unique <= max_cat_cardinality:
                low_card.append(col)
        cat_cols = low_card

    transformers = []
    if numeric_cols:
        num_steps: List = [("imputer", SimpleImputer(strategy="median"))]
        if scale:
            num_steps.append(("scaler", StandardScaler()))
        transformers.append(("num", Pipeline(num_steps), numeric_cols))

    if cat_cols:
        cat_pipeline = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ]
        )
        transformers.append(("cat", cat_pipeline, cat_cols))

    if not transformers:
        raise ValueError("No feature columns available to build the preprocessing pipeline.")

    preprocessor = ColumnTransformer(transformers)
    return preprocessor


__all__ = ["build_tabular_pipeline"]
