import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# =============================================================================
# ALGORITHM RECIPE — how every song is scored against the taste profile
# =============================================================================
#
# OVERVIEW
# --------
# Each song receives a single composite score between 0.0 and 10.0.
# The score is built from six independent sub-scores, each worth a fixed
# maximum number of points. Sub-scores are summed; the top-k songs win.
#
# ┌─────────────────────────┬────────┬───────────────────────────────────────┐
# │ Sub-score               │ Max pts│ Rule                                  │
# ├─────────────────────────┼────────┼───────────────────────────────────────┤
# │ 1. Genre match          │  3.0   │ Exact string match → full 3 pts       │
# │                         │        │ No match           → 0 pts            │
# ├─────────────────────────┼────────┼───────────────────────────────────────┤
# │ 2. Mood match           │  2.0   │ Exact string match → full 2 pts       │
# │                         │        │ No match           → 0 pts            │
# ├─────────────────────────┼────────┼───────────────────────────────────────┤
# │ 3. Energy proximity     │  2.0   │ gap = |song.energy - target_energy|   │
# │                         │        │ gap ≤ tolerance    → full 2 pts       │
# │                         │        │ gap > tolerance    → 2 * (1 - gap)    │
# │                         │        │   (floors at 0)                       │
# ├─────────────────────────┼────────┼───────────────────────────────────────┤
# │ 4. Valence proximity    │  1.0   │ gap = |song.valence - target_valence| │
# │                         │        │ pts = 1.0 * (1 - gap)  (linear decay) │
# ├─────────────────────────┼────────┼───────────────────────────────────────┤
# │ 5. Tempo proximity      │  1.0   │ gap = |song.tempo_bpm - target_bpm|   │
# │                         │        │ normalised_gap = min(gap / 60, 1.0)   │
# │                         │        │ pts = 1.0 * (1 - normalised_gap)      │
# │                         │        │   (60 BPM away = 0 pts)               │
# ├─────────────────────────┼────────┼───────────────────────────────────────┤
# │ 6. Acoustic bonus       │  1.0   │ Only applied when likes_acoustic=True │
# │                         │        │ pts = song.acousticness  (0–1 float)  │
# │                         │        │ When likes_acoustic=False → 0 pts     │
# └─────────────────────────┴────────┴───────────────────────────────────────┘
#
# TOTAL MAX SCORE = 3 + 2 + 2 + 1 + 1 + 1 = 10.0
#
# WORKED EXAMPLE — profile: r&b / sad / energy=0.50 / valence=0.35 /
#                            tempo=85 / likes_acoustic=True / tolerance=0.20
#
#   Song: "Broken Clocks"  (r&b, sad, energy=0.48, valence=0.31, tempo=85,
#                           acousticness=0.55)
#     1. genre   : "r&b" == "r&b"          → 3.0
#     2. mood    : "sad" == "sad"           → 2.0
#     3. energy  : gap=|0.48-0.50|=0.02 ≤ 0.20 → 2.0
#     4. valence : gap=|0.31-0.35|=0.04   → 1.0*(1-0.04) = 0.96
#     5. tempo   : gap=|85-85|=0          → 1.0*(1-0/60)  = 1.0
#     6. acoustic: 0.55                   → 0.55
#     TOTAL = 3.0 + 2.0 + 2.0 + 0.96 + 1.0 + 0.55 = 9.51  ✅ HIGH
#
#   Song: "Storm Runner"   (rock, intense, energy=0.91, valence=0.48,
#                           tempo=152, acousticness=0.10)
#     1. genre   : "rock" != "r&b"         → 0.0
#     2. mood    : "intense" != "sad"       → 0.0
#     3. energy  : gap=|0.91-0.50|=0.41 > 0.20 → 2*(1-0.41) = 1.18
#     4. valence : gap=|0.48-0.35|=0.13   → 1.0*(1-0.13) = 0.87
#     5. tempo   : gap=|152-85|=67 → norm=min(67/60,1)=1.0 → 0.0
#     6. acoustic: likes_acoustic=True, but 0.10 → 0.10
#     TOTAL = 0 + 0 + 1.18 + 0.87 + 0.0 + 0.10 = 2.15  ✅ LOW
#
# RANKING & SELECTION
# --------------------
# 1. score_song() is called once per song → returns (score, [reason strings])
# 2. recommend_songs() sorts all (song, score) pairs descending by score
# 3. The top-k entries are returned with their explanation strings
# 4. Ties are broken by the order songs appear in the CSV (stable sort)
#
# REASON STRINGS (used by explain_recommendation)
# -------------------------------------------------
# Each sub-score that fires adds a plain-English reason, e.g.:
#   "Matches your favorite genre (r&b)"
#   "Matches your preferred mood (sad)"
#   "Energy level (0.48) is close to your target (0.50)"
#   "Valence (0.31) is close to your preference (0.35)"
#   "Tempo (85 BPM) is close to your target (85 BPM)"
#   "Has a strong acoustic feel you prefer"
# =============================================================================


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """Read songs.csv and return a list of dicts with numeric fields cast to int/float."""
    # Columns that should become floats
    FLOAT_COLS = {"energy", "tempo_bpm", "valence", "danceability", "acousticness"}
    # Columns that should become ints
    INT_COLS   = {"id"}

    songs: List[Dict] = []

    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)          # header row used as keys automatically
        for row in reader:
            song: Dict = {}
            for key, value in row.items():
                if key in INT_COLS:
                    song[key] = int(value)
                elif key in FLOAT_COLS:
                    song[key] = float(value)
                else:
                    song[key] = value             # title, artist, genre, mood stay as str
            songs.append(song)

    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Return a (score, reasons) tuple rating one song against the taste profile on six weighted signals."""
    score   = 0.0
    reasons: List[str] = []

    # ------------------------------------------------------------------
    # 1. GENRE MATCH — worth 3.0 pts
    #    Exact string comparison (both lowercased for safety).
    # ------------------------------------------------------------------
    GENRE_PTS = 3.0
    if song["genre"].lower() == user_prefs["favorite_genre"].lower():
        score += GENRE_PTS
        reasons.append(f"genre match (+{GENRE_PTS})")
    else:
        reasons.append(f"genre mismatch: '{song['genre']}' vs '{user_prefs['favorite_genre']}' (+0.0)")

    # ------------------------------------------------------------------
    # 2. MOOD MATCH — worth 2.0 pts
    #    Exact string comparison (lowercased).
    # ------------------------------------------------------------------
    MOOD_PTS = 2.0
    if song["mood"].lower() == user_prefs["favorite_mood"].lower():
        score += MOOD_PTS
        reasons.append(f"mood match (+{MOOD_PTS})")
    else:
        reasons.append(f"mood mismatch: '{song['mood']}' vs '{user_prefs['favorite_mood']}' (+0.0)")

    # ------------------------------------------------------------------
    # 3. ENERGY PROXIMITY — worth up to 2.0 pts
    #    gap = |song.energy - target_energy|
    #    If gap is within the tolerance band  → full 2.0 pts
    #    If gap exceeds tolerance             → 2.0 * (1 - gap), floored at 0
    # ------------------------------------------------------------------
    ENERGY_PTS  = 2.0
    tolerance   = user_prefs.get("energy_tolerance", 0.20)
    energy_gap  = abs(song["energy"] - user_prefs["target_energy"])

    if energy_gap <= tolerance:
        energy_score = ENERGY_PTS
    else:
        energy_score = max(0.0, ENERGY_PTS * (1.0 - energy_gap))

    score += energy_score
    reasons.append(
        f"energy {song['energy']:.2f} vs target {user_prefs['target_energy']:.2f} "
        f"(gap {energy_gap:.2f}) (+{energy_score:.2f})"
    )

    # ------------------------------------------------------------------
    # 4. VALENCE PROXIMITY — worth up to 1.0 pts
    #    Linear decay: pts = 1.0 * (1 - gap)
    #    A song with identical valence scores 1.0; opposite end scores 0.0.
    # ------------------------------------------------------------------
    VALENCE_PTS  = 1.0
    valence_gap  = abs(song["valence"] - user_prefs["target_valence"])
    valence_score = max(0.0, VALENCE_PTS * (1.0 - valence_gap))

    score += valence_score
    reasons.append(
        f"valence {song['valence']:.2f} vs target {user_prefs['target_valence']:.2f} "
        f"(gap {valence_gap:.2f}) (+{valence_score:.2f})"
    )

    # ------------------------------------------------------------------
    # 5. TEMPO PROXIMITY — worth up to 1.0 pts
    #    Raw BPM gap is normalised over a 60-BPM window:
    #        normalised_gap = min(gap / 60, 1.0)
    #    pts = 1.0 * (1 - normalised_gap)
    #    60+ BPM away from target = 0 pts; exact match = 1.0 pts.
    # ------------------------------------------------------------------
    TEMPO_PTS       = 1.0
    TEMPO_WINDOW    = 60.0
    tempo_gap       = abs(song["tempo_bpm"] - user_prefs["target_tempo_bpm"])
    norm_tempo_gap  = min(tempo_gap / TEMPO_WINDOW, 1.0)
    tempo_score     = max(0.0, TEMPO_PTS * (1.0 - norm_tempo_gap))

    score += tempo_score
    reasons.append(
        f"tempo {song['tempo_bpm']:.0f} BPM vs target {user_prefs['target_tempo_bpm']:.0f} BPM "
        f"(gap {tempo_gap:.0f}) (+{tempo_score:.2f})"
    )

    # ------------------------------------------------------------------
    # 6. ACOUSTIC BONUS — worth up to 1.0 pts
    #    Only fires when the user explicitly likes acoustic tracks.
    #    pts = song.acousticness (already a 0-1 float).
    # ------------------------------------------------------------------
    ACOUSTIC_PTS = 1.0
    if user_prefs.get("likes_acoustic", False):
        acoustic_score = song["acousticness"] * ACOUSTIC_PTS
        score += acoustic_score
        reasons.append(f"acoustic feel {song['acousticness']:.2f} (you like acoustic) (+{acoustic_score:.2f})")
    else:
        reasons.append("acoustic bonus skipped (likes_acoustic=False) (+0.0)")

    return round(score, 2), reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score all songs with score_song, sort descending, and return the top-k as (song, score, explanation) tuples."""
    # ------------------------------------------------------------------ #
    # STEP 1 — Judge every song: build a flat list of scored tuples.      #
    # List comprehension replaces an explicit for-loop + .append() and    #
    # expresses "transform every element" as a single readable line.      #
    # ------------------------------------------------------------------ #
    scored: List[Tuple[Dict, float, List[str]]] = [
        (song, score, reasons)
        for song in songs
        for score, reasons in (score_song(user_prefs, song),)   # unpack once
    ]

    # ------------------------------------------------------------------ #
    # STEP 2 — Rank: sorted() returns a NEW list; the originals are safe. #
    # key=lambda t: t[1]  tells sorted() to compare on the score field.  #
    # reverse=True        means highest score comes first.                #
    # ------------------------------------------------------------------ #
    ranked: List[Tuple[Dict, float, List[str]]] = sorted(
        scored,
        key=lambda t: t[1],
        reverse=True,
    )

    # ------------------------------------------------------------------ #
    # STEP 3 — Select: slice the top k entries.                           #
    # Join the reason list into one readable string for the caller.       #
    # ------------------------------------------------------------------ #
    return [
        (song, score, " | ".join(reasons))
        for song, score, reasons in ranked[:k]
    ]
