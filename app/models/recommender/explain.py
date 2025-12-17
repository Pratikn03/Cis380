from __future__ import annotations

from typing import Optional

from app.models.recommender.predict import catalog_dataframe


def explain_recommendation(user_id: str, item_id: str) -> str:
    df = catalog_dataframe()
    match = df[df["item_id"] == item_id]
    if match.empty:
        return "Recommended based on general similarity."
    row = match.iloc[0]
    parts = []
    if row["category"]:
        parts.append(f"{row['category']} category")
    if row["brand"]:
        parts.append(f"brand {row['brand']}")
    reason = " · ".join(parts) or "shared metadata"
    return f"Recommended because it shares {reason} with your query."
