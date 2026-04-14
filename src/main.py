"""
Command line runner for the Music Recommender Simulation.

Run from the project root:
    python -m src.main

Two profiles are demonstrated:
    1. POP_HAPPY_PROFILE   — the "default" verification profile
    2. USER_TASTE_PROFILE  — the primary r&b/sad taste profile
"""

import sys, os
# Allow both `python src/main.py` and `python -m src.main` to find recommender.py
sys.path.insert(0, os.path.dirname(__file__))
from recommender import load_songs, recommend_songs

# ---------------------------------------------------------------------------
# TASTE PROFILES
# ---------------------------------------------------------------------------

# Profile 1 — default verification profile (pop / happy)
# Expected top results: Sunrise City, Rooftop Lights, Gym Hero
POP_HAPPY_PROFILE = {
    "favorite_genre":      "pop",
    "favorite_mood":       "happy",
    "target_energy":       0.80,
    "target_valence":      0.80,
    "target_tempo_bpm":    120,
    "target_danceability": 0.80,
    "likes_acoustic":      False,
    "energy_tolerance":    0.20,
}

# Profile 2 — primary profile used throughout development (r&b / sad)
# Expected top result: Broken Clocks
USER_TASTE_PROFILE = {
    "favorite_genre":      "r&b",
    "favorite_mood":       "sad",
    "target_energy":       0.50,
    "target_valence":      0.35,
    "target_tempo_bpm":    85,
    "target_danceability": 0.60,
    "likes_acoustic":      True,
    "energy_tolerance":    0.20,
}

# ---------------------------------------------------------------------------
# OUTPUT FORMATTER
# ---------------------------------------------------------------------------

BAR_WIDTH   = 10   # characters wide for the score bar
MAX_SCORE   = 10.0
DIVIDER     = "-" * 60
HEADER_LINE = "=" * 60


def _score_bar(score: float) -> str:
    """
    Render a simple ASCII progress bar proportional to score / MAX_SCORE.
    Example: score 7.5  ->  [#######...]
    """
    filled = round((score / MAX_SCORE) * BAR_WIDTH)
    empty  = BAR_WIDTH - filled
    return f"[{'#' * filled}{'.' * empty}]"


def print_recommendations(profile: dict, songs: list, k: int = 5) -> None:
    """
    Run the recommender for `profile` and print a formatted results block.
    """
    genre = profile["favorite_genre"]
    mood  = profile["favorite_mood"]

    print(HEADER_LINE)
    print(f"  Music Recommender  --  Top {k} picks")
    print(HEADER_LINE)
    print(f"  Genre   : {genre}         Mood    : {mood}")
    print(f"  Energy  : {profile['target_energy']:.2f}          "
          f"Valence : {profile['target_valence']:.2f}")
    print(f"  Tempo   : {profile['target_tempo_bpm']} BPM       "
          f"Acoustic: {'Yes' if profile['likes_acoustic'] else 'No'}")
    print(HEADER_LINE)
    print()

    results = recommend_songs(profile, songs, k=k)

    for rank, (song, score, explanation) in enumerate(results, start=1):
        bar = _score_bar(score)

        print(f"  #{rank}  {song['title']}")
        print(f"       Artist : {song['artist']}")
        print(f"       Genre  : {song['genre']}  |  Mood : {song['mood']}")
        print(f"       Score  : {score:.2f} / {MAX_SCORE:.1f}  {bar}")
        print(f"       Reasons:")

        # Each reason is pipe-separated — split and indent for readability
        for reason in explanation.split(" | "):
            print(f"         + {reason}")

        print(f"  {DIVIDER}")

    print()


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"\nCatalog loaded: {len(songs)} songs\n")

    print_recommendations(POP_HAPPY_PROFILE, songs, k=5)


if __name__ == "__main__":
    main()
