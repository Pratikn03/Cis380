"""Configuration for external APIs (optional)."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class APIConfig:
    tmdb_api_key: str | None
    news_api_key: str | None
    places_api_key: str | None


def load_config() -> APIConfig:
    """Read API keys from environment variables; leave None if missing."""
    return APIConfig(
        tmdb_api_key=os.getenv("TMDB_API_KEY"),
        news_api_key=os.getenv("NEWS_API_KEY"),
        places_api_key=os.getenv("PLACES_API_KEY") or os.getenv("FOURSQUARE_API_KEY"),
    )


__all__ = ["APIConfig", "load_config"]
