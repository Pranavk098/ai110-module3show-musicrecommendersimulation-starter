"""
Command line runner for the Music Recommender Simulation.

Run from the project root:
    python -m src.main

Five profiles are demonstrated, including two adversarial edge cases.
All four scoring modes and the diversity-aware ranker are shown.

Usage:
    python -m src.main                  # runs all profiles (full demo)
    python -m src.main [profile_num]    # runs a single profile (1–5)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from recommender import load_songs, recommend_songs, recommend_songs_with_diversity, SCORING_MODES

try:
    from tabulate import tabulate
    _TABULATE_AVAILABLE = True
except ImportError:
    _TABULATE_AVAILABLE = False

# ===========================================================================
# TASTE PROFILES
# ===========================================================================

# Profile 1 — High-Energy Pop (standard, upbeat listener)
HIGH_ENERGY_POP = {
    "name": "High-Energy Pop",
    "favorite_genre":         "pop",
    "favorite_mood":          "happy",
    "target_energy":          0.85,
    "target_valence":         0.85,
    "target_tempo_bpm":       125,
    "target_danceability":    0.85,
    "likes_acoustic":         False,
    "energy_tolerance":       0.15,
    "target_popularity":      88,
    "target_decade":          2020,
    "target_mood_tag":        "euphoric",
    "target_instrumentalness": 0.02,
    "target_speechiness":     0.05,
}

# Profile 2 — Chill Lofi (study/focus listener)
CHILL_LOFI = {
    "name": "Chill Lofi",
    "favorite_genre":         "lofi",
    "favorite_mood":          "chill",
    "target_energy":          0.38,
    "target_valence":         0.58,
    "target_tempo_bpm":       76,
    "target_danceability":    0.60,
    "likes_acoustic":         True,
    "energy_tolerance":       0.15,
    "target_popularity":      68,
    "target_decade":          2020,
    "target_mood_tag":        "dreamy",
    "target_instrumentalness": 0.65,
    "target_speechiness":     0.03,
}

# Profile 3 — Deep Intense Rock (headbanger listener)
DEEP_ROCK = {
    "name": "Deep Intense Rock",
    "favorite_genre":         "rock",
    "favorite_mood":          "intense",
    "target_energy":          0.92,
    "target_valence":         0.45,
    "target_tempo_bpm":       150,
    "target_danceability":    0.65,
    "likes_acoustic":         False,
    "energy_tolerance":       0.10,
    "target_popularity":      75,
    "target_decade":          2010,
    "target_mood_tag":        "aggressive",
    "target_instrumentalness": 0.08,
    "target_speechiness":     0.07,
}

# Profile 4 — ADVERSARIAL: Conflicting Preferences
#   High energy (0.9) but sad mood — these rarely co-occur in real music.
#   The system should surface songs with high energy but penalise non-sad moods.
CONFLICTING_PREFS = {
    "name": "Adversarial: High Energy + Sad Mood",
    "favorite_genre":         "r&b",
    "favorite_mood":          "sad",
    "target_energy":          0.90,   # contradicts "sad" (sad songs are usually low energy)
    "target_valence":         0.20,
    "target_tempo_bpm":       140,
    "target_danceability":    0.80,
    "likes_acoustic":         False,
    "energy_tolerance":       0.10,
    "target_mood_tag":        "melancholic",
}

# Profile 5 — ADVERSARIAL: Ultra-Niche Taste
#   Classical/calm with very low energy — tests the catalog's coverage limits.
NICHE_CLASSICAL = {
    "name": "Adversarial: Ultra-Niche Classical",
    "favorite_genre":         "classical",
    "favorite_mood":          "calm",
    "target_energy":          0.18,
    "target_valence":         0.75,
    "target_tempo_bpm":       55,
    "target_danceability":    0.25,
    "likes_acoustic":         True,
    "energy_tolerance":       0.10,
    "target_popularity":      60,
    "target_decade":          2000,
    "target_mood_tag":        "serene",
    "target_instrumentalness": 0.90,
    "target_speechiness":     0.02,
}

ALL_PROFILES = [
    HIGH_ENERGY_POP,
    CHILL_LOFI,
    DEEP_ROCK,
    CONFLICTING_PREFS,
    NICHE_CLASSICAL,
]

# ===========================================================================
# OUTPUT FORMATTING — Visual Summary Table (Challenge 4)
# ===========================================================================

MAX_SCORE = 12.5   # base 10 + up to 2.5 extended bonus
BAR_WIDTH  = 10
DIVIDER    = "-" * 70
HEADER     = "=" * 70


def _score_bar(score: float, max_score: float = MAX_SCORE) -> str:
    filled = round((score / max_score) * BAR_WIDTH)
    empty  = BAR_WIDTH - filled
    return f"[{'#' * filled}{'.' * empty}]"


def _print_profile_header(profile: dict, mode: str) -> None:
    name = profile.get("name", "Unknown Profile")
    print(HEADER)
    print(f"  PROFILE: {name}")
    print(f"  Mode   : {mode.upper()}")
    print(HEADER)
    print(f"  Genre   : {profile['favorite_genre']:<12}  Mood    : {profile['favorite_mood']}")
    print(f"  Energy  : {profile['target_energy']:.2f}          Valence : {profile['target_valence']:.2f}")
    print(f"  Tempo   : {profile['target_tempo_bpm']} BPM       Acoustic: {'Yes' if profile['likes_acoustic'] else 'No'}")
    if "target_mood_tag" in profile:
        print(f"  Mood Tag: {profile['target_mood_tag']:<12}  Decade  : {profile.get('target_decade', 'any')}")
    print(HEADER)
    print()


def _print_table(results: list, profile_name: str) -> None:
    """Print results as a formatted table using tabulate (or ASCII fallback)."""
    headers = ["Rank", "Title", "Artist", "Genre", "Mood", "Score", "Bar", "Key Reason"]

    rows = []
    for rank, (song, score, explanation) in enumerate(results, start=1):
        # Extract the first meaningful reason (skip mismatches if possible)
        reason_parts = explanation.split(" | ")
        key_reason = next(
            (r for r in reason_parts if "match" in r and "mismatch" not in r),
            reason_parts[0],
        )
        rows.append([
            f"#{rank}",
            song["title"],
            song["artist"],
            song["genre"],
            song["mood"],
            f"{score:.2f}",
            _score_bar(score),
            key_reason,
        ])

    if _TABULATE_AVAILABLE:
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    else:
        # ASCII fallback — simple column-aligned table
        col_widths = [max(len(str(row[i])) for row in rows + [headers]) for i in range(len(headers))]
        sep = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"
        def fmt_row(row):
            return "| " + " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row))) + " |"
        print(sep)
        print(fmt_row(headers))
        print(sep)
        for row in rows:
            print(fmt_row(row))
        print(sep)
    print()


def _print_detail_reasons(results: list) -> None:
    """Print the full reason breakdown for each recommendation."""
    for rank, (song, score, explanation) in enumerate(results, start=1):
        print(f"  #{rank}  {song['title']}  --  {score:.2f} pts  {_score_bar(score)}")
        print(f"       Artist : {song['artist']}  |  Genre : {song['genre']}  |  Mood : {song['mood']}")
        print(f"       Reasons:")
        for reason in explanation.split(" | "):
            print(f"         + {reason}")
        print(f"  {DIVIDER}")
    print()


def print_recommendations(
    profile: dict,
    songs: list,
    k: int = 5,
    mode: str = "balanced",
    use_diversity: bool = False,
    diversity_penalty: float = 1.5,
) -> None:
    """Run the recommender for a profile and print formatted results."""
    _print_profile_header(profile, mode)

    if use_diversity:
        results = recommend_songs_with_diversity(profile, songs, k=k, mode=mode,
                                                 diversity_penalty=diversity_penalty)
        print(f"  [Diversity Mode ON — artist penalty: -{diversity_penalty} pts per repeat]\n")
    else:
        results = recommend_songs(profile, songs, k=k, mode=mode)

    _print_table(results, profile["name"])
    _print_detail_reasons(results)


# ===========================================================================
# EXPERIMENT: Weight-Shift Demo (Phase 4, Step 3)
# Doubles energy importance vs. balanced mode using "energy-focused" mode.
# ===========================================================================

def print_mode_comparison(profile: dict, songs: list, k: int = 5) -> None:
    """Show how changing scoring mode shifts the recommendations."""
    print(HEADER)
    print(f"  EXPERIMENT: Scoring-Mode Comparison  —  {profile.get('name', '')}")
    print(HEADER)
    print()

    for mode in SCORING_MODES:
        results = recommend_songs(profile, songs, k=k, mode=mode)
        titles = [f"#{i+1} {s['title']} ({sc:.1f})" for i, (s, sc, _) in enumerate(results)]
        weight_summary = ", ".join(
            f"{k}={v}" for k, v in SCORING_MODES[mode].items()
        )
        print(f"  [{mode.upper()}]  Weights: {weight_summary}")
        print(f"    " + "  |  ".join(titles))
        print()


# ===========================================================================
# ENTRY POINT
# ===========================================================================

def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"\nCatalog loaded: {len(songs)} songs\n")

    # Determine which profile(s) to run
    if len(sys.argv) > 1:
        try:
            idx = int(sys.argv[1]) - 1
            profiles_to_run = [ALL_PROFILES[idx]]
        except (ValueError, IndexError):
            print(f"Usage: python -m src.main [1-{len(ALL_PROFILES)}]")
            sys.exit(1)
    else:
        profiles_to_run = ALL_PROFILES

    # -------------------------------------------------------------------
    # Run each profile in balanced mode (for screenshots)
    # -------------------------------------------------------------------
    for profile in profiles_to_run:
        print_recommendations(profile, songs, k=5, mode="balanced")

    if len(profiles_to_run) > 1:
        # -------------------------------------------------------------------
        # Show all four scoring modes for profile 1 (High-Energy Pop)
        # -------------------------------------------------------------------
        print_mode_comparison(HIGH_ENERGY_POP, songs, k=5)

        # -------------------------------------------------------------------
        # Show diversity-aware mode for profile 1
        # -------------------------------------------------------------------
        print_recommendations(
            HIGH_ENERGY_POP, songs, k=5, mode="balanced",
            use_diversity=True, diversity_penalty=1.5
        )

        # -------------------------------------------------------------------
        # Experimental: energy-focused mode for the conflicting profile
        # -------------------------------------------------------------------
        print(HEADER)
        print("  EXPERIMENT: Energy-Focused Mode on Conflicting Profile")
        print("  (Energy weight doubled vs balanced; mood weight halved)")
        print(HEADER)
        print()
        print_recommendations(CONFLICTING_PREFS, songs, k=5, mode="energy-focused")


if __name__ == "__main__":
    main()
