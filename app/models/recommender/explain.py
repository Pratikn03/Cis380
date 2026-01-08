from __future__ import annotations

import random

from app.models.recommender.predict import catalog_dataframe


# Varied explanation templates for more natural responses
EXPLANATION_TEMPLATES = [
    "This is a great pick because it shares {reason} with your interests.",
    "Recommended for you based on {reason}.",
    "You might enjoy this - it matches your preference for {reason}.",
    "A solid choice featuring {reason}.",
    "Selected because of {reason} - a popular choice!",
    "Based on {reason}, this should be a good fit for you.",
    "This recommendation matches your {reason} interests.",
]

GENERIC_EXPLANATIONS = [
    "A highly-rated option that many users enjoy.",
    "Popular choice with excellent reviews.",
    "Trending recommendation in this category.",
    "Well-regarded option based on user ratings.",
    "Top pick based on overall popularity.",
    "Frequently recommended by similar users.",
    "A crowd favorite in this category.",
]


def explain_recommendation(user_id: str, item_id: str) -> str:
    """Generate a varied explanation for why an item was recommended."""
    df = catalog_dataframe()
    match = df[df["item_id"] == item_id]
    
    if match.empty:
        return random.choice(GENERIC_EXPLANATIONS)
    
    row = match.iloc[0]
    parts = []
    
    if row["category"]:
        parts.append(f"{row['category']}")
    if row["brand"]:
        parts.append(f"{row['brand']} brand")
    
    if parts:
        reason = " and ".join(parts)
        template = random.choice(EXPLANATION_TEMPLATES)
        return template.format(reason=reason)
    
    return random.choice(GENERIC_EXPLANATIONS)
