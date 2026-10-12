# Smart Shuffle Algorithm Documentation

## Overview

This document defines the ML-powered Smart Shuffle algorithm for Superior Spotify - a weighted recommendation system that combines personal listening preferences, audio feature similarity, and diversity considerations to create a superior shuffle experience beyond Spotify's basic random playback.

---

## What We Know from Planning Docs

### Core ML Requirements

The Smart Shuffle system must deliver:

1. **Personalized Track Scoring** - Each candidate track receives a weighted score based on multiple factors
2. **Context-Aware Selection** - Account for mood, time of day, and listening session type
3. **Diversity Enforcement** - Prevent artist/album clustering and ensure variety
4. **Exploration Mechanism** - Balance familiarity with discovery of new tracks
5. **Preference Learning** - Adapt based on user behavior (skips, repeats, full plays)

### ML Architecture (from Planning)

```
INPUT LAYER
  Listen events, skips, repeats, likes, playlist additions
       │
       ▼
┌─────────────────┐    ┌─────────────────┐
│COLLABORATIVE    │    │CONTENT-BASED    │
│- Item similarity│    │- Audio feature  │
│- Listening patt │    │- MFCC/Chroma    │
└────────┬────────┘    └────────┬────────┘
         │                      │
         └──────────┬───────────┘
                    ▼
          ┌─────────────────┐
          │ HYBRID SCORING  │
          │ - Weighted      │
          │ - Session context│
          │ - Temporal fact.│
          └────────┬────────┘
                   ▼
          ┌─────────────────┐
          │DIVERSITY LAYER  │
          │ - MMR re-ranking│
          │ - Artist spread │
          │ - Recent history│
          └────────┬────────┘
                   ▼
          ┌─────────────────┐
          │WEIGHTED SAMPLING│
          │ - Softmax       │
          │ - Bandit        │
          └─────────────────┘
```

---

## Sources

This documentation synthesizes the following planning documents:

| Document | Path | Key Sections Referenced |
|----------|------|------------------------|
| Comprehensive Plan | `planning/comprehensive-plan.md` | ML Architecture, Audio Features Available, Smart Shuffle Algorithm |
| Architecture | `planning/architecture.md` | ML considerations, technical stack |
| Spotify API Docs | External | Audio features documentation |

---

## Audio Features Reference

Spotify provides **11 audio features** for every track. These form the embedding space for all similarity calculations.

### Normalized Features (0-1 scale)

| Feature | Range | Meaning | Use Case in Smart Shuffle |
|---------|-------|---------|---------------------------|
| **danceability** | 0-1 | Beat strength, rhythm stability | Match energy level of current session |
| **energy** | 0-1 | Intensity, loudness, dynamics | Balance high/low energy in playlist |
| **valence** | 0-1 | Musical positiveness (happy→sad) | Mood matching, emotional consistency |
| **acousticness** | 0-1 | Confidence track is acoustic | Electronic vs. acoustic balance |
| **instrumentalness** | 0-1 | Likelihood of no vocals | Focus/background vs. vocal emphasis |
| **liveness** | 0-1 | Presence of audience | Live vs. studio feel preference |
| **speechiness** | 0-1 | Presence of spoken words | Genre detection (rap vs. singing) |

### Non-Normalized Features

| Feature | Range | Meaning | Use Case in Smart Shuffle |
|---------|-------|---------|---------------------------|
| **tempo** | BPM (not bounded) | Beats per minute | Energy matching, workout compatibility |
| **loudness** | dB (typically -60 to 0) | Volume level | Volume normalization awareness |
| **mode** | 0 or 1 | Minor (0) vs Major (1) | Mood indicator (minor=melancholy) |
| **key** | 0-11 (pitch class) | Musical key (0=C, 1=C#, etc.) | Harmonic compatibility for transitions |

### Feature Vector Representation

A track is represented as a 11-dimensional vector:

```
track_vector = [
    danceability, energy, valence, acousticness,
    instrumentalness, liveness, speechiness,
    tempo_normalized, loudness_normalized,
    mode, key_normalized
]
```

**Note**: Tempo and loudness must be normalized before similarity calculations.

---

## Similarity Calculations

### Cosine Similarity

**Primary similarity metric** for comparing tracks in audio feature space.

**Formula:**

```
cosine_similarity(A, B) = (A · B) / (||A|| × ||B||)

Where:
- A · B = Σ(aᵢ × bᵢ)  (dot product)
- ||A|| = √(Σ aᵢ²)    (Euclidean norm)
- ||B|| = √(Σ bᵢ²)
```

**Range:** -1 to 1 (1 = identical, 0 = orthogonal, -1 = opposite)

**For audio features (all positive), range is effectively 0 to 1.**

### Implementation (Python/scikit-learn)

```python
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def calculate_track_similarity(track_a_features, track_b_features):
    """
    Calculate cosine similarity between two tracks.

    Args:
        track_a_features: numpy array of shape (11,) or (1, 11)
        track_b_features: numpy array of shape (11,) or (1, 11)

    Returns:
        float: Similarity score (0 to 1)
    """
    # Ensure 2D arrays for scikit-learn
    a = np.array(track_a_features).reshape(1, -1)
    b = np.array(track_b_features).reshape(1, -1)

    similarity = cosine_similarity(a, b)[0][0]
    return similarity
```

### Batch Similarity Calculation

```python
def find_similar_tracks(
    target_track_features: np.ndarray,
    candidate_tracks: np.ndarray,
    n_results: int = 10
) -> List[Tuple[str, float]]:
    """
    Find the n most similar tracks to a target.

    Args:
        target_track_features: Target track feature vector (11,)
        candidate_tracks: Array of shape (n_tracks, 11) with all candidate features
        n_results: Number of results to return

    Returns:
        List of (track_id, similarity_score) tuples, sorted descending
    """
    similarities = cosine_similarity(
        target_track_features.reshape(1, -1),
        candidate_tracks
    )[0]

    # Get top n indices
    top_indices = similarities.argsort()[-n_results:][::-1]

    return [(track_ids[i], similarities[i]) for i in top_indices]
```

### Feature Weighting (Optional Enhancement)

Not all features contribute equally to perceived similarity:

```python
def weighted_cosine_similarity(A, B, weights=None):
    """
    Calculate weighted cosine similarity.

    Default weights emphasize perceptually important features.
    """
    if weights is None:
        # Higher weights for more important features
        weights = np.array([
            1.2,  # danceability (important)
            1.1,  # energy (important)
            1.3,  # valence (mood - very important)
            0.8,  # acousticness
            0.7,  # instrumentalness
            0.5,  # liveness (less important)
            0.6,  # speechiness
            1.0,  # tempo
            0.5,  # loudness
            0.8,  # mode
            0.7   # key
        ])

    weighted_A = A * weights
    weighted_B = B * weights

    return np.dot(weighted_A, weighted_B) / (
        np.linalg.norm(weighted_A) * np.linalg.norm(weighted_B)
    )
```

---

## Smart Shuffle Scoring

### Core Formula

The overall score for a track in smart shuffle:

```
score(track) = α × play_frequency + β × audio_similarity +
               γ × diversity_bonus - δ × recency_penalty + ε × exploration_bonus
```

### Component Breakdown

#### 1. Play Frequency (weight: α = 0.35)

How often the user has played this track historically.

```python
def play_frequency_score(track_id, user_id, db_connection):
    """
    Calculate play frequency score (0-1).
    Normalized by total plays to handle user behavior differences.
    """
    query = """
        SELECT COUNT(*) as track_plays,
               (SELECT COUNT(*) FROM listening_events WHERE user_id = ?) as total_plays
        FROM listening_events
        WHERE user_id = ? AND track_id = ?
    """

    result = db_connection.execute(query, (user_id, user_id, track_id)).fetchone()

    if result.total_plays == 0:
        return 0.0

    # Use log scaling to prevent overfamiliar tracks from dominating
    raw_score = result.track_plays / max(result.total_plays, 1)
    return min(math.log1p(raw_score * 100) / math.log1p(100), 1.0)
```

#### 2. Audio Similarity (weight: β = 0.30)

How well the track matches the user's preferred audio profile.

```python
def audio_similarity_score(track_features, user_profile_features):
    """
    Calculate similarity to user's preferred audio profile.

    user_profile_features: Average or weighted average of user's liked tracks
    """
    return cosine_similarity(
        [track_features],
        [user_profile_features]
    )[0][0]
```

**User Profile Calculation:**

```python
def calculate_user_audio_profile(user_id, db_connection, window_days=90):
    """
    Calculate user's preferred audio profile from recent listening.
    Weighted by completion rate (full plays > skips).
    """
    query = """
        SELECT af.danceability, af.energy, af.valence, af.acousticness,
               af.instrumentalness, af.liveness, af.speechiness,
               af.tempo, af.loudness, af.mode, af.key,
               le.position_ms, tr.duration_ms
        FROM listening_events le
        JOIN audio_features af ON le.track_id = af.track_id
        JOIN tracks tr ON le.track_id = tr.id
        WHERE le.user_id = ?
          AND le.played_at > datetime('now', '-{} days')
        ORDER BY le.id DESC
        LIMIT 500
    """.format(window_days)

    tracks = db_connection.execute(query, (user_id,)).fetchall()

    if not tracks:
        return DEFAULT_USER_PROFILE

    # Weight by completion rate
    weights = []
    feature_vectors = []

    for track in tracks:
        completion = min(track.position_ms / max(track.duration_ms, 1), 1.0)
        weights.append(completion)

        vec = [
            track.danceability, track.energy, track.valence,
            track.acousticness, track.instrumentalness, track.liveness,
            track.speechiness, track.tempo / 200,  # Normalize to 0-1
            track.loudness / 60,  # Normalize to 0-1
            track.mode, track.key / 11
        ]
        feature_vectors.append(vec)

    # Weighted average
    weights = np.array(weights)
    weights /= weights.sum()

    profile = np.average(feature_vectors, axis=0, weights=weights)
    return profile
```

#### 3. Diversity Bonus (weight: γ = 0.20)

Penalty for artist/album clustering, bonus for variety.

```python
def diversity_bonus(track, recent_history, window_minutes=60):
    """
    Calculate diversity bonus based on recent playback history.

    Prevents consecutive plays from the same artist or album.
    """
    artist_penalty = 0.0
    album_penalty = 0.0

    for recent_track in recent_history:
        time_diff = (recent_played_at - track.played_at).total_seconds() / 60

        if time_diff > window_minutes:
            break

        if recent_track.artist_id == track.artist_id:
            artist_penalty += 1.0

        if recent_track.album_id == track.album_id:
            album_penalty += 0.5

    # Exponential decay for penalties
    diversity_score = 1.0 / (1.0 + artist_penalty * 2.0 + album_penalty)

    return diversity_score
```

#### 4. Recency Penalty (weight: δ = 0.10)

Penalize recently played tracks to encourage variety.

```python
def recency_penalty(track_last_played, current_time):
    """
    Calculate recency penalty based on time since last play.
    """
    if track_last_played is None:
        return 0.0  # Never played, no penalty

    days_since_played = (current_time - track_last_played).days

    # Log decay - less penalty the longer ago
    if days_since_played == 0:
        return 1.0  # Strong penalty for same day

    return min(days_since_played / 30, 1.0)  # Max penalty after 30 days

def recency_bonus(track_last_played, current_time):
    """Inverse of penalty - bonus for not recently played"""
    return 1.0 - recency_penalty(track_last_played, current_time)
```

#### 5. Exploration Bonus (weight: ε = 0.05)

Bonus for discovering new tracks (Ucb1-style exploration).

```python
def exploration_bonus(track_id, user_id, total_plays):
    """
    Multi-armed bandit exploration bonus.
    Encourages trying underplayed tracks.

    UCB1-style: encourages exploration of less-seen options
    """
    # Count plays of this specific track
    query = """
        SELECT COUNT(*) FROM listening_events
        WHERE user_id = ? AND track_id = ?
    """
    track_plays = db_connection.execute(
        query, (user_id, track_id)
    ).fetchone()[0]

    if track_plays == 0:
        # Never played - maximum exploration bonus
        return 1.0

    # Decay based on plays (logarithmic)
    bonus = 1.0 / math.log1p(track_plays * 10)

    return min(bonus, 1.0)
```

### Final Scoring Function

```python
def smart_shuffle_score(
    track,
    user_id,
    user_profile,
    recent_history,
    db_connection,
    current_time
) -> float:
    """
    Calculate overall smart shuffle score for a track.

    Returns: float (0-100 scale for readability)
    """
    # 1. Play Frequency (α = 0.35)
    play_freq = play_frequency_score(track.id, user_id, db_connection)

    # 2. Audio Similarity (β = 0.30)
    audio_sim = audio_similarity_score(
        track.audio_features,
        user_profile
    )

    # 3. Diversity Bonus (γ = 0.20)
    diversity = diversity_bonus(track, recent_history)

    # 4. Recency (δ = 0.10) - bonus for NOT recently played
    recency = recency_bonus(track.last_played, current_time)

    # 5. Exploration (ε = 0.05)
    exploration = exploration_bonus(track.id, user_id, total_plays)

    # Combine with weights
    raw_score = (
        0.35 * play_freq +
        0.30 * audio_sim +
        0.20 * diversity +
        0.10 * recency +
        0.05 * exploration
    )

    return raw_score * 100  # Scale to 0-100
```

### Weighted Random Selection

After scoring, use softmax-weighted sampling for final selection:

```python
import random
from scipy.special import softmax

def weighted_selection(tracks_with_scores, temperature=1.0):
    """
    Select a track using softmax-weighted sampling.

    Temperature controls exploration:
    - High temp (2.0+): More random, more exploration
    - Low temp (0.5): More deterministic, favors top scores
    """
    scores = np.array([t['score'] for t in tracks_with_scores])

    # Apply temperature
    scaled_scores = scores / temperature

    # Softmax probabilities
    probs = softmax(scaled_scores)

    # Weighted random choice
    selected_idx = np.random.choice(len(tracks_with_scores), p=prob
```

[... truncated for brevity ...]
