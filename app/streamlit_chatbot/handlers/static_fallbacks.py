"""Static fallback recommendations when APIs are unavailable - with randomization."""

from __future__ import annotations

import random
from typing import List, Dict

# ============================================================================
# MOVIE FALLBACKS - Large pool for variety
# ============================================================================
MOVIES_POOL = [
    # Action
    {
        "title": "The Dark Knight (2008)",
        "reason": "Christopher Nolan's masterpiece; genre: Action/Crime",
        "genre": "action",
    },
    {
        "title": "Mad Max: Fury Road (2015)",
        "reason": "Non-stop action spectacle; genre: Action/Sci-Fi",
        "genre": "action",
    },
    {
        "title": "John Wick (2014)",
        "reason": "Stylish action thriller; genre: Action/Thriller",
        "genre": "action",
    },
    {
        "title": "Die Hard (1988)",
        "reason": "Classic action film; genre: Action/Thriller",
        "genre": "action",
    },
    {
        "title": "Gladiator (2000)",
        "reason": "Epic historical action; genre: Action/Drama",
        "genre": "action",
    },
    {
        "title": "The Matrix (1999)",
        "reason": "Revolutionary sci-fi action; genre: Action/Sci-Fi",
        "genre": "action",
    },
    {
        "title": "Terminator 2 (1991)",
        "reason": "Iconic sequel; genre: Action/Sci-Fi",
        "genre": "action",
    },
    # Sci-Fi
    {
        "title": "Inception (2010)",
        "reason": "Mind-bending thriller; genre: Sci-Fi/Action",
        "genre": "sci-fi",
    },
    {
        "title": "Interstellar (2014)",
        "reason": "Epic space exploration; genre: Sci-Fi/Drama",
        "genre": "sci-fi",
    },
    {
        "title": "Blade Runner 2049 (2017)",
        "reason": "Stunning visual sci-fi; genre: Sci-Fi/Drama",
        "genre": "sci-fi",
    },
    {
        "title": "Arrival (2016)",
        "reason": "Intelligent alien contact story; genre: Sci-Fi/Drama",
        "genre": "sci-fi",
    },
    {
        "title": "Ex Machina (2014)",
        "reason": "Thought-provoking AI thriller; genre: Sci-Fi/Thriller",
        "genre": "sci-fi",
    },
    {
        "title": "The Martian (2015)",
        "reason": "Survival on Mars; genre: Sci-Fi/Adventure",
        "genre": "sci-fi",
    },
    # Comedy
    {
        "title": "The Grand Budapest Hotel (2014)",
        "reason": "Quirky Wes Anderson comedy; genre: Comedy/Drama",
        "genre": "comedy",
    },
    {
        "title": "Superbad (2007)",
        "reason": "Hilarious coming-of-age; genre: Comedy",
        "genre": "comedy",
    },
    {
        "title": "The Hangover (2009)",
        "reason": "Wild comedy adventure; genre: Comedy",
        "genre": "comedy",
    },
    {
        "title": "Bridesmaids (2011)",
        "reason": "Laugh-out-loud comedy; genre: Comedy",
        "genre": "comedy",
    },
    {
        "title": "Groundhog Day (1993)",
        "reason": "Classic Bill Murray comedy; genre: Comedy/Fantasy",
        "genre": "comedy",
    },
    {
        "title": "Dumb and Dumber (1994)",
        "reason": "Slapstick classic; genre: Comedy",
        "genre": "comedy",
    },
    # Drama
    {
        "title": "The Shawshank Redemption (1994)",
        "reason": "All-time classic; genre: Drama",
        "genre": "drama",
    },
    {
        "title": "Forrest Gump (1994)",
        "reason": "Heartwarming journey; genre: Drama/Romance",
        "genre": "drama",
    },
    {
        "title": "The Godfather (1972)",
        "reason": "Legendary crime drama; genre: Drama/Crime",
        "genre": "drama",
    },
    {
        "title": "Schindler's List (1993)",
        "reason": "Powerful historical drama; genre: Drama/History",
        "genre": "drama",
    },
    {
        "title": "Fight Club (1999)",
        "reason": "Cult classic thriller; genre: Drama/Thriller",
        "genre": "drama",
    },
    {
        "title": "Pulp Fiction (1994)",
        "reason": "Tarantino masterpiece; genre: Drama/Crime",
        "genre": "drama",
    },
    # Horror
    {
        "title": "Get Out (2017)",
        "reason": "Social horror thriller; genre: Horror/Thriller",
        "genre": "horror",
    },
    {
        "title": "A Quiet Place (2018)",
        "reason": "Tense survival horror; genre: Horror/Thriller",
        "genre": "horror",
    },
    {
        "title": "The Shining (1980)",
        "reason": "Kubrick horror classic; genre: Horror",
        "genre": "horror",
    },
    {
        "title": "Hereditary (2018)",
        "reason": "Disturbing family horror; genre: Horror/Drama",
        "genre": "horror",
    },
    {"title": "It (2017)", "reason": "Stephen King adaptation; genre: Horror", "genre": "horror"},
    # Animation
    {
        "title": "Spider-Man: Into the Spider-Verse (2018)",
        "reason": "Groundbreaking animation; genre: Animation/Action",
        "genre": "animation",
    },
    {
        "title": "Toy Story (1995)",
        "reason": "Pixar's first masterpiece; genre: Animation/Comedy",
        "genre": "animation",
    },
    {
        "title": "Finding Nemo (2003)",
        "reason": "Heartwarming adventure; genre: Animation/Family",
        "genre": "animation",
    },
    {
        "title": "The Incredibles (2004)",
        "reason": "Superhero family fun; genre: Animation/Action",
        "genre": "animation",
    },
    {
        "title": "Coco (2017)",
        "reason": "Beautiful Day of the Dead story; genre: Animation/Family",
        "genre": "animation",
    },
    # Thriller
    {
        "title": "Se7en (1995)",
        "reason": "Dark detective thriller; genre: Thriller/Crime",
        "genre": "thriller",
    },
    {
        "title": "Gone Girl (2014)",
        "reason": "Twisty psychological thriller; genre: Thriller/Drama",
        "genre": "thriller",
    },
    {
        "title": "Parasite (2019)",
        "reason": "Oscar-winning thriller; genre: Thriller/Drama",
        "genre": "thriller",
    },
    {
        "title": "Zodiac (2007)",
        "reason": "Gripping true crime; genre: Thriller/Crime",
        "genre": "thriller",
    },
    {
        "title": "Silence of the Lambs (1991)",
        "reason": "Classic psychological horror; genre: Thriller/Horror",
        "genre": "thriller",
    },
]


def movies_fallback(query: str) -> List[Dict]:
    """Return random movie recommendations based on query."""
    query_lower = query.lower()

    # Check for genre keywords
    genre_map = {
        "action": "action",
        "sci-fi": "sci-fi",
        "scifi": "sci-fi",
        "science fiction": "sci-fi",
        "comedy": "comedy",
        "funny": "comedy",
        "laugh": "comedy",
        "drama": "drama",
        "serious": "drama",
        "horror": "horror",
        "scary": "horror",
        "frightening": "horror",
        "animation": "animation",
        "animated": "animation",
        "cartoon": "animation",
        "thriller": "thriller",
        "suspense": "thriller",
    }

    target_genre = None
    for keyword, genre in genre_map.items():
        if keyword in query_lower:
            target_genre = genre
            break

    # Filter by genre if specified
    if target_genre:
        filtered = [m for m in MOVIES_POOL if m.get("genre") == target_genre]
        if filtered:
            selected = random.sample(filtered, min(5, len(filtered)))
            return [{"title": m["title"], "reason": m["reason"]} for m in selected]

    # Random selection from all movies
    selected = random.sample(MOVIES_POOL, min(5, len(MOVIES_POOL)))
    return [{"title": m["title"], "reason": m["reason"]} for m in selected]


# ============================================================================
# PLACES FALLBACKS
# ============================================================================
PLACES_POOL = [
    {"title": "Central Park Coffee", "reason": "Cozy cafe with great reviews; 4.5★"},
    {"title": "The Rustic Kitchen", "reason": "Farm-to-table dining; 4.7★"},
    {"title": "Skyline Rooftop Bar", "reason": "Amazing city views; 4.4★"},
    {"title": "Green Leaf Bistro", "reason": "Healthy options available; 4.6★"},
    {"title": "The Book Nook Cafe", "reason": "Quiet atmosphere, great coffee; 4.5★"},
    {"title": "Harbor View Restaurant", "reason": "Waterfront dining; 4.6★"},
    {"title": "City Art Museum", "reason": "World-class exhibitions; 4.8★"},
    {"title": "Riverside Park", "reason": "Beautiful walking trails; 4.7★"},
    {"title": "The Jazz Corner", "reason": "Live music nightly; 4.5★"},
    {"title": "Urban Food Hall", "reason": "Diverse food options; 4.4★"},
]


def places_fallback(query: str) -> List[Dict]:
    """Return random place recommendations."""
    selected = random.sample(PLACES_POOL, min(5, len(PLACES_POOL)))
    return [{"title": p["title"], "reason": p["reason"]} for p in selected]


# ============================================================================
# NEWS FALLBACKS
# ============================================================================
NEWS_POOL = {
    "general": [
        {
            "title": "Breaking: Major Tech Company Announces Innovation",
            "reason": "Top story; Technology",
        },
        {"title": "Global Summit Addresses Climate Change", "reason": "World news; Environment"},
        {"title": "Stock Markets Reach New Highs", "reason": "Business; Finance"},
        {"title": "New Scientific Discovery Announced", "reason": "Science; Research"},
        {"title": "Sports Championship Finals This Weekend", "reason": "Sports; Entertainment"},
    ],
    "health": [
        {
            "title": "New Treatment Shows Promise for Chronic Disease",
            "reason": "Medical breakthrough; Health",
        },
        {"title": "Study Reveals Benefits of Mediterranean Diet", "reason": "Nutrition; Wellness"},
        {"title": "Mental Health Awareness Campaign Launches", "reason": "Mental health; Society"},
        {"title": "Exercise Routine for Busy Professionals", "reason": "Fitness; Lifestyle"},
        {"title": "Sleep Quality Linked to Productivity", "reason": "Research; Health"},
    ],
    "crime": [
        {
            "title": "Cybersecurity Alert: New Phishing Scam Detected",
            "reason": "Security; Technology",
        },
        {"title": "Law Enforcement Announces Major Operation", "reason": "Crime; Justice"},
        {"title": "Identity Theft Prevention Tips", "reason": "Security; Consumer"},
        {"title": "Fraud Prevention Measures Updated", "reason": "Finance; Security"},
        {"title": "Community Safety Initiative Launched", "reason": "Local; Safety"},
    ],
    "tech": [
        {
            "title": "AI Breakthrough: New Model Achieves Human-Level Performance",
            "reason": "AI; Technology",
        },
        {"title": "Major Software Update Brings New Features", "reason": "Software; Tech"},
        {"title": "Startup Raises Record Funding Round", "reason": "Business; Tech"},
        {"title": "New Smartphone Features Revealed", "reason": "Mobile; Consumer tech"},
        {"title": "Cloud Computing Trends for 2026", "reason": "Enterprise; Technology"},
    ],
}


def news_fallback(query: str, topic: str | None = None) -> List[Dict]:
    """Return random news based on topic."""
    if topic and topic.lower() in NEWS_POOL:
        pool = NEWS_POOL[topic.lower()]
    else:
        # Combine all news
        pool = []
        for news_list in NEWS_POOL.values():
            pool.extend(news_list)

    selected = random.sample(pool, min(5, len(pool)))
    return selected


# ============================================================================
# CARS FALLBACKS
# ============================================================================
CARS_POOL = [
    {"title": "Tesla Model 3", "reason": "Best-selling EV; 358mi range; $40K+"},
    {"title": "Tesla Model Y", "reason": "Popular electric SUV; spacious; $44K+"},
    {"title": "Toyota RAV4", "reason": "Reliable compact SUV; great resale; $28K+"},
    {"title": "Honda CR-V", "reason": "Practical family SUV; fuel efficient; $29K+"},
    {"title": "Toyota Camry", "reason": "Dependable sedan; excellent value; $26K+"},
    {"title": "Honda Civic", "reason": "Sporty compact; great MPG; $24K+"},
    {"title": "Ford F-150", "reason": "Best-selling truck; versatile; $33K+"},
    {"title": "BMW 3 Series", "reason": "Luxury sports sedan; refined; $43K+"},
    {"title": "Mercedes C-Class", "reason": "Premium comfort; elegant; $44K+"},
    {"title": "Mazda CX-5", "reason": "Fun to drive SUV; upscale interior; $27K+"},
    {"title": "Hyundai Tucson", "reason": "Feature-rich value; 10yr warranty; $28K+"},
    {"title": "Kia Telluride", "reason": "Award-winning 3-row SUV; $35K+"},
]


def cars_fallback(query: str) -> List[Dict]:
    """Return random car recommendations."""
    selected = random.sample(CARS_POOL, min(5, len(CARS_POOL)))
    return [{"title": c["title"], "reason": c["reason"]} for c in selected]


# ============================================================================
# COURSES FALLBACKS
# ============================================================================
COURSES_POOL = [
    {"title": "Machine Learning A-Z", "reason": "Comprehensive ML course; Udemy bestseller"},
    {
        "title": "Python for Data Science",
        "reason": "Learn pandas, numpy, sklearn; beginner-friendly",
    },
    {"title": "Deep Learning Specialization", "reason": "Andrew Ng's famous course; Coursera"},
    {"title": "Full Stack Web Development", "reason": "React, Node.js, MongoDB; career-ready"},
    {"title": "AWS Certified Solutions Architect", "reason": "Cloud certification prep; in-demand"},
    {"title": "Cybersecurity Fundamentals", "reason": "Security basics; CompTIA prep"},
    {"title": "Data Structures & Algorithms", "reason": "Interview prep; coding mastery"},
    {"title": "Product Management 101", "reason": "PM skills; career transition"},
]


def courses_fallback(query: str) -> List[Dict]:
    """Return random course recommendations."""
    selected = random.sample(COURSES_POOL, min(5, len(COURSES_POOL)))
    return [{"title": c["title"], "reason": c["reason"]} for c in selected]


# ============================================================================
# BOOKS FALLBACKS
# ============================================================================
BOOKS_POOL = [
    {"title": "The Hobbit", "reason": "Classic fantasy adventure; J.R.R. Tolkien"},
    {"title": "1984", "reason": "Dystopian masterpiece; George Orwell"},
    {"title": "To Kill a Mockingbird", "reason": "Timeless courtroom drama; Harper Lee"},
    {"title": "The Name of the Wind", "reason": "Epic fantasy; Patrick Rothfuss"},
    {"title": "Pride and Prejudice", "reason": "Beloved romance; Jane Austen"},
    {"title": "The Martian", "reason": "Smart sci-fi survival; Andy Weir"},
    {"title": "Sapiens", "reason": "Big-picture history; Yuval Noah Harari"},
    {"title": "The Alchemist", "reason": "Inspirational journey; Paulo Coelho"},
]


def books_fallback(query: str) -> List[Dict]:
    """Return random book recommendations."""
    selected = random.sample(BOOKS_POOL, min(5, len(BOOKS_POOL)))
    return [{"title": b["title"], "reason": b["reason"]} for b in selected]


# ============================================================================
# GAMES FALLBACKS
# ============================================================================
GAMES_POOL = [
    {"title": "Hades", "reason": "Fast-paced roguelike; critically acclaimed"},
    {"title": "Stardew Valley", "reason": "Relaxing farming sim; cozy vibes"},
    {"title": "Hollow Knight", "reason": "Challenging metroidvania; great art"},
    {"title": "The Witcher 3: Wild Hunt", "reason": "Epic RPG; deep story"},
    {"title": "Celeste", "reason": "Tight platformer; inspiring narrative"},
    {"title": "Portal 2", "reason": "Puzzle classic; witty writing"},
    {"title": "Factorio", "reason": "Automation addicting loop; strategy"},
    {"title": "Slay the Spire", "reason": "Deck-builder roguelike; highly replayable"},
]


def games_fallback(query: str) -> List[Dict]:
    """Return random game recommendations."""
    selected = random.sample(GAMES_POOL, min(5, len(GAMES_POOL)))
    return [{"title": g["title"], "reason": g["reason"]} for g in selected]


__all__ = [
    "movies_fallback",
    "places_fallback",
    "news_fallback",
    "cars_fallback",
    "courses_fallback",
    "books_fallback",
    "games_fallback",
]
