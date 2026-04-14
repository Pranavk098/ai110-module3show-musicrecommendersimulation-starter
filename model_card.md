# 🎧 Model Card: VibeFinder 2.0

---

## 1. Model Name

**VibeFinder 2.0** — a content-based music recommender simulation built for the CodePath AI-110 Module 3 project.

---

## 2. Goal / Task

VibeFinder 2.0 suggests songs from a curated catalog that best match a user's current taste profile. It takes a description of what the user wants to hear right now — their preferred genre, mood, energy level, tempo, and acoustic character — and returns the top-5 songs that score highest against those preferences.

The goal is not to predict what a user *will* like based on history. Instead, it maps explicit, measurable preferences to measurable song features and ranks the best matches. Think of it as a "describe your vibe right now and I'll find it" tool.

---

## 3. How the Model Works

### The short version

Every song in the catalog gets a single number called a **composite score**. The song with the highest score becomes recommendation #1, the second-highest becomes #2, and so on. The top 5 are returned.

### How the score is built

The score adds up points from eleven separate signals. The first six are the **base signals** (worth up to 10 points total); the remaining five are **extended bonus signals** (worth up to 2.5 additional points).

**Base signals:**

1. **Genre match** — If the song's genre label exactly matches the user's favorite genre, it earns up to 3 points (in balanced mode). No match means 0 points. This is the biggest single signal.

2. **Mood match** — If the song's mood label exactly matches the user's preferred mood, it earns up to 2 points. This is all-or-nothing: "sad" and "melancholic" are treated as completely different even though they feel similar.

3. **Energy proximity** — The system measures the gap between the song's energy level (0–1 scale) and the user's target energy. If the gap is small (within a "tolerance band"), the song earns full points. Larger gaps earn proportionally fewer points.

4. **Valence proximity** — Valence measures musical positivity (1 = very upbeat, 0 = somber). The closer the song's valence is to the user's target, the more points it earns, using a straight linear formula.

5. **Tempo proximity** — The gap between the song's BPM and the user's target BPM is measured. A gap of 60+ BPM earns 0 points; exact match earns full points.

6. **Acoustic bonus** — If the user likes acoustic music, songs with higher acousticness scores earn more points. If the user doesn't care about acoustics, this signal is ignored entirely.

**Extended bonus signals (Challenge 1):**

7. **Popularity proximity** — Rewards songs near the user's preferred popularity level (0–100 scale).
8. **Release decade match** — Awards a bonus if the song was released in the user's preferred decade.
9. **Detailed mood tag match** — A finer mood check (e.g., "euphoric" vs. "dreamy") beyond the broad mood label.
10. **Instrumentalness proximity** — Rewards songs close to the user's preference for vocal vs. fully instrumental tracks.
11. **Speechiness proximity** — Rewards songs close to the user's preference for spoken-word or rap content.

### Scoring modes (Challenge 2)

The same eleven signals are available in four **scoring modes** that redistribute the base 10 points differently:

| Mode | Genre | Mood | Energy | Valence | Tempo | Acoustic |
|---|---|---|---|---|---|---|
| balanced | 3.0 | 2.0 | 2.0 | 1.0 | 1.0 | 1.0 |
| genre-first | 5.0 | 1.0 | 1.5 | 0.8 | 0.7 | 1.0 |
| mood-first | 1.5 | 4.5 | 1.5 | 1.0 | 0.8 | 0.7 |
| energy-focused | 1.5 | 1.5 | 5.0 | 0.5 | 0.8 | 0.7 |

### Diversity penalty (Challenge 3)

By default, the ranker picks purely by score, which can result in two songs by the same artist in the top 5. The diversity mode subtracts **1.5 points** from a song's effective score every time its artist has already appeared in the selected list. This nudges variety without ignoring score entirely.

---

## 4. Data Used

The catalog lives in `data/songs.csv` and contains **18 songs** with **15 attributes each**.

**Original 10 attributes:** id, title, artist, genre, mood, energy (0–1), tempo_bpm, valence (0–1), danceability (0–1), acousticness (0–1).

**5 new attributes added (Phase 4):** popularity (0–100), release_decade (e.g. 2000, 2010, 2020), mood_tag (detailed string like "euphoric" or "melancholic"), instrumentalness (0–1), speechiness (0–1).

**Genres represented:** pop, lofi, rock, ambient, jazz, synthwave, indie pop, country, latin, metal, gospel, r&b, electronic, folk, classical.

**Moods represented:** happy, chill, intense, relaxed, focused, moody, nostalgic, euphoric, angry, uplifting, sad, energetic, melancholic, calm.

**Known gaps:** The catalog skews heavily toward Western popular genres. Hip-hop, reggae, blues, and non-English music are absent. Sad high-energy songs are nearly non-existent — the catalog reflects a real-world correlation where sad mood almost always implies low energy.

---

## 5. Strengths

**Works well for users whose taste matches well-represented genres.** Profiles built around pop, lofi, or rock reliably surface intuitive results. For a pop/happy listener, "Sunrise City" consistently ranks #1 with a score above 11/12.5 — exactly what a human DJ would pick first.

**Fully transparent scoring.** Every recommendation prints a plain-English reason for each sub-score. Unlike black-box deep learning models, VibeFinder can always explain precisely why a song ranked where it did, making it easy to debug and trust.

**Modular scoring modes let users control what matters.** Switching from `balanced` to `energy-focused` visibly shifts the rankings in a predictable, explainable way. This makes the system a good teaching tool for understanding how weight choices drive output.

**Adversarial profiles expose flaws rather than hiding them.** The system doesn't silently fail — when given contradictory preferences (high energy + sad mood), it still returns results with correct logic and clearly labeled reasons, making the limitation observable rather than mysterious.

---

## 6. Observed Behavior / Biases

**Genre dominates everything.** In balanced mode, genre is worth 3 out of 10 points — more than any other single signal. A song that matches genre but misses mood will almost always outscore a song that matches mood but misses genre. This is intentional but leads to a known problem: two songs in completely different emotional "feels" (say, an upbeat pop banger vs. a sad pop ballad) look equally attractive to the ranker as long as both say "pop."

**Mood is binary and brittle.** The mood match is an exact string comparison. "Melancholic" earns zero credit when the user asks for "sad," even though the words are nearly synonymous. Any variation in how the catalog tags emotions leads to unexpected gaps.

**Acoustic signal is one-sided.** The acoustic bonus only helps users who like acoustic music. A user who actively prefers electronic production gets no benefit from this dimension.

**Small catalog amplifies representation bias.** With only 18 songs, any genre that appears 3+ times has a structural advantage. Users who like lofi get three songs to choose from; users who like classical get one. This means a classical fan's top-5 will be padded with songs that missed the genre entirely — the system simply runs out of good matches.

**Filter bubble risk.** Without diversity mode, back-to-back songs by the same artist (e.g., two LoRoom lofi tracks) can both appear in the top 5. In a real product this would feel repetitive. The diversity penalty feature (Challenge 3) partially addresses this.

---

## 7. Evaluation Process

### Profiles tested

Five user profiles were tested, including two adversarial edge cases:

| # | Profile | Description |
|---|---|---|
| 1 | High-Energy Pop | Standard upbeat listener — pop, happy, high energy |
| 2 | Chill Lofi | Study session listener — lofi, chill, low energy, acoustic |
| 3 | Deep Intense Rock | Headbanger — rock, intense, very high energy |
| 4 | Adversarial: Conflicting | r&b genre but high energy (0.90) + sad mood — real r&b sad songs are low-energy, so this profile fights itself |
| 5 | Adversarial: Classical | Classical, calm, very low energy — tests catalog coverage limits |

### What we looked for

- Do the top results match the intuitive "right answer" for each profile?
- Does changing the scoring mode meaningfully shift the recommendations?
- Does the diversity penalty actually prevent artist repetition?
- Does the adversarial profile expose flaws in the scoring logic?

### What surprised us

**Profile 4 (High Energy + Sad):** The system had no r&b song that is both high-energy and sad. "Broken Clocks" (the only r&b/sad song) earned the genre and mood bonus but lost many energy points because its energy (0.48) is far from the target (0.90). Songs from completely different genres ended up ranked above it purely on energy proximity. This confirmed that **the energy gap can overpower genre+mood alignment** when the conflict is large enough.

**Profile 5 (Classical):** The system correctly put "Inner Peace" at rank #1 (it's the only classical song and has all the right numeric attributes). But ranks #2–5 were completely unrelated genres because the catalog doesn't have enough calm, low-energy, acoustic songs. The system wasn't "wrong" by its own logic, but the results weren't useful.

**Mode comparison (High-Energy Pop):** Switching from balanced to genre-first kept the top result the same (Sunrise City), but the #2 and #3 positions swapped between Gym Hero and Rooftop Lights depending on whether genre or mood was weighted higher. This shows that the system is sensitive to mode even for clear-cut profiles.

---

## 8. Intended Use and Non-Intended Use

**Intended use:**
- Classroom demonstration of content-based filtering concepts
- Exploring how scoring weights affect recommendation output
- Understanding where bias can enter a simple rule-based system

**Not intended for:**
- Real production music recommendation (catalog too small, no user history)
- Drawing conclusions about real listeners' preferences
- Replacing collaborative filtering or deep learning approaches

---

## 9. Ideas for Improvement

1. **Expand and balance the catalog.** 18 songs is not enough. Doubling to 36–50 songs with equal genre representation would make all profiles meaningful.

2. **Fuzzy mood matching.** Replace binary mood comparison with a similarity table (e.g., "sad" and "melancholic" share 80% credit). This would remove the biggest brittleness in the current logic.

3. **Collaborative filtering layer.** Add implicit feedback (e.g., "this song was skipped" or "played 3 times") and combine it with the content scores. Real recommenders use both signals.

4. **Learned weights.** Instead of hardcoding the weights (genre = 3.0, mood = 2.0, etc.), let users implicitly tune them over several recommendation sessions based on which songs they liked.

5. **Richer diversity logic.** Extend the diversity penalty to also consider genre and mood — so the top 5 always contains a mix of at least 3 different genres even if same-genre songs score slightly higher.

---

## 10. Personal Reflection

Building VibeFinder made concrete something that otherwise stays abstract: recommender systems are just a formalized version of "what features matter and how much." The hard part isn't the math (which is straightforward weighted addition) — it's deciding *which* features to measure and *how much* each one should count. Every weight in the scoring table is an editorial choice, and those choices encode values. Prioritizing genre over mood means we're saying "what kind of music you want matters more than how you feel." That might be wrong for a listener who wants sad songs regardless of genre.

Using AI tools (Copilot / Claude) during development was genuinely helpful for generating the initial scoring skeleton and suggesting edge cases to test (like the conflicting high-energy + sad profile). However, the AI couldn't tell me *whether the results made sense* — that required musical intuition and manually checking each profile's output against expectations. The adversarial profiles were particularly revealing: the tool passed all its own tests while producing recommendations that no real listener would want. This reinforced a key lesson: **tests verify correctness of logic, not usefulness of output**.

The most surprising discovery was how much a tiny catalog amplifies bias. With 18 songs, any genre with 3+ entries has a structural advantage over genres with only 1 entry. No amount of tuning the scoring weights can fix a classical fan's experience when there's literally one classical song in the database. Real-world recommenders solve this with massive catalogs — our system shows exactly *why* that matters.

If I extended this project, I would first fix the catalog representation problem, then add fuzzy mood matching, and then experiment with learned weights using simulated user feedback. Those three changes would make VibeFinder useful rather than merely correct.
