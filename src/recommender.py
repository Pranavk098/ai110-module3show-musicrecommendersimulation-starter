import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

# =============================================================================
# SCORING MODES — define how much each sub-score signal is worth
# =============================================================================
#
# Four ranking strategies are supported. Each mode redistributes the same
# 10 points across the six base signals so that a different attribute
# "leads" the ranking. The weights in each mode sum to 10.0.
#
#  balanced      – Equal priority (default); used for general listeners
#  genre-first   – Genre dominates; useful when genre matters most
#  mood-first    – Mood dominates; useful when emotional state drives the listen
#  energy-focused– Energy dominates; useful for workout or focus playlists
#
# Extended attributes (popularity, release_decade, mood_tag,
# instrumentalness, speechiness) are always scored as a bonus on top of the
# base 10.0 and can add up to 2.5 additional points.
# =============================================================================

SCORING_MODES: Dict[str, Dict[str, float]] = {
    "balanced": {
        "genre": 3.0, "mood": 2.0, "energy": 2.0,
        "valence": 1.0, "tempo": 1.0, "acoustic": 1.0,
    },
    "genre-first": {
        "genre": 5.0, "mood": 1.0, "energy": 1.5,
        "valence": 0.8, "tempo": 0.7, "acoustic": 1.0,
    },
    "mood-first": {
        "genre": 1.5, "mood": 4.5, "energy": 1.5,
        "valence": 1.0, "tempo": 0.8, "acoustic": 0.7,
    },
    "energy-focused": {
        "genre": 1.5, "mood": 1.5, "energy": 5.0,
        "valence": 0.5, "tempo": 0.8, "acoustic": 0.7,
    },
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py

    Base attributes (original):
        id, title, artist, genre, mood, energy, tempo_bpm,
        valence, danceability, acousticness

    Extended attributes (Phase 4 additions):
        popularity       — 0-100 chart popularity score
        release_decade   — decade of release (e.g. 2010, 2020)
        mood_tag         — detailed mood label (e.g. "euphoric", "melancholic")
        instrumentalness — 0-1 fraction of the track that is instrumental
        speechiness      — 0-1 fraction of spoken word / rap content
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
    # Extended attributes — default values keep the test suite backward-compatible
    popularity: int = 70
    release_decade: int = 2010
    mood_tag: str = ""
    instrumentalness: float = 0.0
    speechiness: float = 0.05


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


# =============================================================================
# OOP RECOMMENDER CLASS
# =============================================================================

class Recommender:
    """
    OOP wrapper around the functional scoring/ranking pipeline.
    Required by tests/test_recommender.py
    """

    def __init__(self, songs: List[Song]):
        self.songs = songs

    def _song_to_dict(self, song: Song) -> Dict:
        return {
            "id": song.id, "title": song.title, "artist": song.artist,
            "genre": song.genre, "mood": song.mood, "energy": song.energy,
            "tempo_bpm": song.tempo_bpm, "valence": song.valence,
            "danceability": song.danceability, "acousticness": song.acousticness,
            "popularity": song.popularity, "release_decade": song.release_decade,
            "mood_tag": song.mood_tag, "instrumentalness": song.instrumentalness,
            "speechiness": song.speechiness,
        }

    def _profile_to_dict(self, user: UserProfile) -> Dict:
        return {
            "favorite_genre": user.favorite_genre,
            "favorite_mood": user.favorite_mood,
            "target_energy": user.target_energy,
            "target_valence": 0.5,
            "target_tempo_bpm": 100,
            "likes_acoustic": user.likes_acoustic,
            "energy_tolerance": 0.20,
        }

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return top-k Song objects sorted by score (highest first)."""
        user_dict = self._profile_to_dict(user)
        song_dicts = [self._song_to_dict(s) for s in self.songs]
        results = recommend_songs(user_dict, song_dicts, k=k)
        # Map back to Song objects by title
        title_to_song = {s.title: s for s in self.songs}
        return [title_to_song[song_dict["title"]] for song_dict, _, _ in results]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable explanation for why this song was recommended."""
        user_dict = self._profile_to_dict(user)
        song_dict = self._song_to_dict(song)
        _, reasons = score_song(user_dict, song_dict)
        return " | ".join(reasons)


# =============================================================================
# DATA LOADING
# =============================================================================

def load_songs(csv_path: str) -> List[Dict]:
    """Read songs.csv and return a list of dicts with numeric fields cast."""
    FLOAT_COLS = {
        "energy", "tempo_bpm", "valence", "danceability",
        "acousticness", "instrumentalness", "speechiness",
    }
    INT_COLS = {"id", "popularity", "release_decade"}

    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            song: Dict = {}
            for key, value in row.items():
                if key in INT_COLS:
                    song[key] = int(value)
                elif key in FLOAT_COLS:
                    song[key] = float(value)
                else:
                    song[key] = value
            songs.append(song)
    return songs


# =============================================================================
# CORE SCORING FUNCTION
# =============================================================================

def score_song(
    user_prefs: Dict,
    song: Dict,
    mode: str = "balanced",
) -> Tuple[float, List[str]]:
    """
    Score one song against a taste profile, returning (score, reasons).

    Base sub-scores use weights from SCORING_MODES[mode] (sum to 10.0).
    Extended sub-scores add up to 2.5 bonus points when the user profile
    includes the matching preference keys.

    Parameters
    ----------
    user_prefs : dict  — taste profile (see main.py for field names)
    song       : dict  — one row from songs.csv (loaded by load_songs)
    mode       : str   — one of "balanced", "genre-first", "mood-first",
                         "energy-focused"
    """
    weights = SCORING_MODES.get(mode, SCORING_MODES["balanced"])
    score: float = 0.0
    reasons: List[str] = []

    # ------------------------------------------------------------------
    # 1. GENRE MATCH — binary, worth weights["genre"] pts
    # ------------------------------------------------------------------
    genre_pts = weights["genre"]
    if song["genre"].lower() == user_prefs["favorite_genre"].lower():
        score += genre_pts
        reasons.append(f"genre match (+{genre_pts})")
    else:
        reasons.append(
            f"genre mismatch: '{song['genre']}' vs '{user_prefs['favorite_genre']}' (+0.0)"
        )

    # ------------------------------------------------------------------
    # 2. MOOD MATCH — binary, worth weights["mood"] pts
    # ------------------------------------------------------------------
    mood_pts = weights["mood"]
    if song["mood"].lower() == user_prefs["favorite_mood"].lower():
        score += mood_pts
        reasons.append(f"mood match (+{mood_pts})")
    else:
        reasons.append(
            f"mood mismatch: '{song['mood']}' vs '{user_prefs['favorite_mood']}' (+0.0)"
        )

    # ------------------------------------------------------------------
    # 3. ENERGY PROXIMITY — worth up to weights["energy"] pts
    #    Within tolerance band → full points; beyond → linear decay
    # ------------------------------------------------------------------
    energy_max = weights["energy"]
    tolerance = user_prefs.get("energy_tolerance", 0.20)
    energy_gap = abs(song["energy"] - user_prefs["target_energy"])

    if energy_gap <= tolerance:
        energy_score = energy_max
    else:
        energy_score = max(0.0, energy_max * (1.0 - energy_gap))

    score += energy_score
    reasons.append(
        f"energy {song['energy']:.2f} vs target {user_prefs['target_energy']:.2f} "
        f"(gap {energy_gap:.2f}) (+{energy_score:.2f})"
    )

    # ------------------------------------------------------------------
    # 4. VALENCE PROXIMITY — worth up to weights["valence"] pts
    #    Linear decay: pts = max_pts * (1 - gap)
    # ------------------------------------------------------------------
    valence_max = weights["valence"]
    valence_gap = abs(song["valence"] - user_prefs["target_valence"])
    valence_score = max(0.0, valence_max * (1.0 - valence_gap))

    score += valence_score
    reasons.append(
        f"valence {song['valence']:.2f} vs target {user_prefs['target_valence']:.2f} "
        f"(gap {valence_gap:.2f}) (+{valence_score:.2f})"
    )

    # ------------------------------------------------------------------
    # 5. TEMPO PROXIMITY — worth up to weights["tempo"] pts
    #    Normalised over 60 BPM window; 60+ BPM away = 0 pts
    # ------------------------------------------------------------------
    tempo_max = weights["tempo"]
    tempo_gap = abs(song["tempo_bpm"] - user_prefs["target_tempo_bpm"])
    norm_tempo_gap = min(tempo_gap / 60.0, 1.0)
    tempo_score = max(0.0, tempo_max * (1.0 - norm_tempo_gap))

    score += tempo_score
    reasons.append(
        f"tempo {song['tempo_bpm']:.0f} BPM vs target {user_prefs['target_tempo_bpm']:.0f} BPM "
        f"(gap {tempo_gap:.0f}) (+{tempo_score:.2f})"
    )

    # ------------------------------------------------------------------
    # 6. ACOUSTIC BONUS — worth up to weights["acoustic"] pts
    #    Only fires when likes_acoustic=True
    # ------------------------------------------------------------------
    acoustic_max = weights["acoustic"]
    if user_prefs.get("likes_acoustic", False):
        acoustic_score = song["acousticness"] * acoustic_max
        score += acoustic_score
        reasons.append(
            f"acoustic feel {song['acousticness']:.2f} (you like acoustic) (+{acoustic_score:.2f})"
        )
    else:
        reasons.append("acoustic bonus skipped (likes_acoustic=False) (+0.0)")

    # ==================================================================
    # EXTENDED ATTRIBUTE BONUSES (Phase 4 — Challenge 1)
    # Each extended feature adds up to 0.5 bonus points.
    # These fire only when the user profile includes the matching key.
    # ==================================================================

    # ------------------------------------------------------------------
    # 7. POPULARITY BONUS — up to 0.5 pts
    #    Rewards songs near the user's target popularity level.
    #    gap normalised over 100-point scale.
    # ------------------------------------------------------------------
    if "target_popularity" in user_prefs and "popularity" in song:
        pop_gap = abs(song["popularity"] - user_prefs["target_popularity"]) / 100.0
        pop_score = max(0.0, 0.5 * (1.0 - pop_gap))
        score += pop_score
        reasons.append(
            f"popularity {song['popularity']} vs target {user_prefs['target_popularity']} "
            f"(+{pop_score:.2f})"
        )

    # ------------------------------------------------------------------
    # 8. RELEASE DECADE MATCH — 0.5 pts for exact decade match
    # ------------------------------------------------------------------
    if "target_decade" in user_prefs and "release_decade" in song:
        if song["release_decade"] == user_prefs["target_decade"]:
            score += 0.5
            reasons.append(
                f"release decade {song['release_decade']} matches target (+0.50)"
            )
        else:
            reasons.append(
                f"release decade {song['release_decade']} vs target {user_prefs['target_decade']} (+0.0)"
            )

    # ------------------------------------------------------------------
    # 9. DETAILED MOOD TAG MATCH — 0.5 pts for exact tag match
    #    More granular than the binary mood check above.
    # ------------------------------------------------------------------
    if "target_mood_tag" in user_prefs and "mood_tag" in song:
        if song["mood_tag"].lower() == user_prefs["target_mood_tag"].lower():
            score += 0.5
            reasons.append(
                f"mood tag '{song['mood_tag']}' matches target (+0.50)"
            )
        else:
            reasons.append(
                f"mood tag '{song['mood_tag']}' vs target '{user_prefs['target_mood_tag']}' (+0.0)"
            )

    # ------------------------------------------------------------------
    # 10. INSTRUMENTALNESS PROXIMITY — up to 0.5 pts
    #     Linear decay over the 0-1 range.
    # ------------------------------------------------------------------
    if "target_instrumentalness" in user_prefs and "instrumentalness" in song:
        inst_gap = abs(song["instrumentalness"] - user_prefs["target_instrumentalness"])
        inst_score = max(0.0, 0.5 * (1.0 - inst_gap))
        score += inst_score
        reasons.append(
            f"instrumentalness {song['instrumentalness']:.2f} vs target "
            f"{user_prefs['target_instrumentalness']:.2f} (+{inst_score:.2f})"
        )

    # ------------------------------------------------------------------
    # 11. SPEECHINESS PROXIMITY — up to 0.5 pts
    #     Rewards rap/spoken-word fans (high speechiness) or
    #     purely sung music fans (low speechiness).
    # ------------------------------------------------------------------
    if "target_speechiness" in user_prefs and "speechiness" in song:
        speech_gap = abs(song["speechiness"] - user_prefs["target_speechiness"])
        speech_score = max(0.0, 0.5 * (1.0 - speech_gap))
        score += speech_score
        reasons.append(
            f"speechiness {song['speechiness']:.2f} vs target "
            f"{user_prefs['target_speechiness']:.2f} (+{speech_score:.2f})"
        )

    return round(score, 2), reasons


# =============================================================================
# STANDARD RECOMMEND FUNCTION (no diversity)
# =============================================================================

def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    mode: str = "balanced",
) -> List[Tuple[Dict, float, str]]:
    """
    Score all songs, sort descending, return top-k as (song, score, explanation).

    Parameters
    ----------
    user_prefs : dict
    songs      : list of song dicts (from load_songs)
    k          : number of results to return
    mode       : scoring mode — "balanced", "genre-first", "mood-first",
                 "energy-focused"
    """
    scored: List[Tuple[Dict, float, List[str]]] = [
        (song, score, reasons)
        for song in songs
        for score, reasons in (score_song(user_prefs, song, mode),)
    ]

    ranked = sorted(scored, key=lambda t: t[1], reverse=True)

    return [
        (song, score, " | ".join(reasons))
        for song, score, reasons in ranked[:k]
    ]


# =============================================================================
# DIVERSITY-AWARE RECOMMEND FUNCTION (Challenge 3)
# =============================================================================

def recommend_songs_with_diversity(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    mode: str = "balanced",
    diversity_penalty: float = 1.5,
) -> List[Tuple[Dict, float, str]]:
    """
    Greedy diversity-aware ranking.

    After each song is tentatively selected, any remaining songs by the same
    artist have their effective score reduced by `diversity_penalty` per
    previous appearance of that artist. This prevents the top-k list from
    being dominated by a single artist.

    Parameters
    ----------
    diversity_penalty : points deducted per prior artist appearance
                        (default 1.5 — enough to push duplicates below
                        a comparable song from a different artist)
    """
    # Step 1 — score everything
    scored = []
    for i, song in enumerate(songs):
        s, reasons = score_song(user_prefs, song, mode)
        scored.append([i, song, s, reasons, False])   # False = not yet picked

    artist_counts: Dict[str, int] = {}
    selected: List[Tuple[Dict, float, str]] = []

    for _ in range(k):
        best_entry = None
        best_adj_score = -1.0
        best_repeat_count = 0

        for entry in scored:
            if entry[4]:            # already selected
                continue
            _, song, base_score, _, _ = entry
            artist = song["artist"]
            count = artist_counts.get(artist, 0)
            adj_score = max(0.0, base_score - diversity_penalty * count)
            if adj_score > best_adj_score:
                best_adj_score = adj_score
                best_entry = entry
                best_repeat_count = count

        if best_entry is None:
            break

        best_entry[4] = True        # mark as selected
        song = best_entry[1]
        base_score = best_entry[2]
        reasons = best_entry[3]
        artist = song["artist"]
        artist_counts[artist] = artist_counts.get(artist, 0) + 1

        penalty_note: List[str] = []
        if best_repeat_count > 0:
            penalty_note = [
                f"diversity penalty -{diversity_penalty * best_repeat_count:.1f} "
                f"(artist '{artist}' already in results)"
            ]

        explanation = " | ".join(reasons + penalty_note)
        selected.append((song, round(best_adj_score, 2), explanation))

    return selected
