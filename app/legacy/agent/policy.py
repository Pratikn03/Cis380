"""Simple keyword-based policy for routing."""

import re


def decide(message: str) -> str:
    text = message.lower()
    tokens = set(re.findall(r"[a-z0-9]+", text))

    if any(k in text for k in ["fraud", "transaction", "card"]):
        return "fraud"
    if any(k in text for k in ["cyber", "network", "attack", "packet"]):
        return "cyber"
    if any(k in text for k in ["behavior", "insider", "employee"]):
        return "behavior"
    # Natural-language recommendations (movies/electronics/places/news) should route to the
    # recommender module even if the user doesn't literally type "recommend".
    if (
        "recommend" in text
        or "suggest" in text
        or tokens.intersection(
            {
                "movie",
                "movies",
                "film",
                "films",
                "romantic",
                "romance",
                "phone",
                "phones",
                "smartphone",
                "smartphones",
                "laptop",
                "laptops",
                "headphone",
                "headphones",
                "earbud",
                "earbuds",
                "car",
                "cars",
                "vehicle",
                "vehicles",
                "suv",
                "sedan",
                "coffee",
                "cafe",
                "restaurant",
                "news",
                "health",
                "crime",
            }
        )
    ):
        return "recommend"
    if any(
        k in text
        for k in [
            "career",
            "careers",
            "skills",
            "role",
            "roles",
            "job",
            "jobs",
            "ml engineer",
            "data scientist",
            "skill map",
        ]
    ):
        return "rag"
    if any(k in text for k in ["doc", "note", "pdf", "paper", "from docs", "rag"]):
        return "rag"
    return "llm"
