"""
Build items.csv (movieId,title,tags,popularity) from archive/movie.csv and rating.csv.

Input:
  - data/raw/archive/movie.csv (movieId,title,genres)
  - data/raw/archive/rating.csv (userId,movieId,rating)

Output:
  - data/raw/recommendation/items.csv

Popularity = count of ratings per movieId.
Tags = genres (pipe-separated) copied from movie.csv
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ARCHIVE_DIR = Path("data/raw/archive")
REC_DIR = Path("data/raw/recommendation")
OUT_FILE = REC_DIR / "items.csv"


def main():
    movie_path = ARCHIVE_DIR / "movie.csv"
    rating_path = ARCHIVE_DIR / "rating.csv"
    if not movie_path.exists() or not rating_path.exists():
        raise FileNotFoundError("Expected movie.csv and rating.csv under data/raw/archive/")

    movies = pd.read_csv(movie_path)
    ratings = pd.read_csv(rating_path, usecols=["movieId"])

    pop = ratings["movieId"].value_counts().rename("popularity")
    movies = movies.rename(columns={"genres": "tags"})
    items = movies[["movieId", "title", "tags"]].copy()
    items = items.merge(pop, left_on="movieId", right_index=True, how="left")
    items["popularity"] = items["popularity"].fillna(0).astype(int)

    REC_DIR.mkdir(parents=True, exist_ok=True)
    items.to_csv(OUT_FILE, index=False)
    print(f"Wrote {OUT_FILE} with {len(items)} rows.")


if __name__ == "__main__":
    main()
