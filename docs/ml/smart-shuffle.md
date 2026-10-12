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

A track is represented as an 11-dimensional vector:

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
        time_diff = (recent_track.played_at - track.played_at).total_seconds() / 60

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

Bonus for discovering new tracks (UCB1-style exploration).

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
    selected_idx = np.random.choice(len(tracks_with_scores), p=probs)
    return tracks_with_scores[selected_idx]
```

---

## ML Techniques

### Content-Based Similarity

The foundation of Smart Shuffle is content-based filtering using audio features:

**Characteristics:**
- **Fast & Explainable**: "Similar to [track] you liked" is easily justified
- **Cold-Start Friendly**: New songs can be recommended immediately
- **No User Data Required**: Works from day one

**Implementation Pattern:**
1. Fetch audio features from Spotify API
2. Cache in local database (features don't change)
3. Compute cosine similarity against target or user profile

### Collaborative Filtering Approach

As user data accumulates, collaborative filtering can supplement content-based methods:

**Item-Item Collaborative Filtering:**
```
"Users who liked X also liked Y"
```

**Implementation:**
- Build co-occurrence matrix from listening events
- Compute conditional probabilities P(like Y | liked X)
- Pre-compute recommendations offline via Celery jobs

**Matrix Factorization (Future Enhancement):**
- Use **implicit** library for ALS (Alternating Least Squares)
- Requires significant user interaction data
- Captures latent taste factors beyond audio features

### Multi-Armed Bandit for Exploration

Balance exploitation (playing what user likes) with exploration (discovery):

**Epsilon-Greedy Strategy:**
```python
def epsilon_greedy_selection(candidates, epsilon=0.1):
    """
    With epsilon probability, choose randomly (explore).
    Otherwise, choose highest score (exploit).
    """
    if random.random() < epsilon:
        return random.choice(candidates)
    return max(candidates, key=lambda t: t.score)
```

**Thompson Sampling (Advanced):**
- Maintain Beta distribution for each track's "like" probability
- Sample from distribution, select highest
- Automatically balances exploration/exploitation

---

## Diversity Layer

### Maximal Marginal Relevance (MMR) Re-Ranking

MMR balances relevance with diversity in ranked results:

```python
def mmr_re_rank(
    ranked_tracks,
    selected_tracks,
    lambda_param=0.7
):
    """
    Re-rank tracks using MMR to maximize relevance-diversity tradeoff.

    MMR score = λ * relevance(track) - (1-λ) * max_similarity(track, selected)

    Args:
        ranked_tracks: Initially ranked tracks by relevance
        selected_tracks: Already selected tracks (for diversity check)
        lambda_param: 1.0 = pure relevance, 0.0 = pure diversity

    Returns:
        Re-ranked list favoring diversity
    """
    mmr_scores = []

    for track in ranked_tracks:
        if track in selected_tracks:
            mmr_scores.append((track, -float('inf')))  # Already selected
            continue

        relevance = track.score  # Original relevance score

        # Max similarity to already selected tracks
        max_sim = 0.0
        for selected in selected_tracks:
            sim = cosine_similarity(track.features, selected.features)
            max_sim = max(max_sim, sim)

        mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim
        mmr_scores.append((track, mmr_score))

    # Sort by MMR score descending
    mmr_scores.sort(key=lambda x: x[1], reverse=True)
    return [t for t, s in mmr_scores]
```

### Artist and Genre Spread

**Hard Constraints:**
```python
def enforce_artist_diversity(tracks, max_consecutive_same_artist=1):
    """
    Ensure no more than N consecutive tracks from same artist.
    """
    result = []
    artist_counts = {}

    for track in tracks:
        artist = track.artist_id

        # Count recent consecutive from same artist
        recent_same_artist = sum(
            1 for t in result[-max_consecutive_same_artist:]
            if t.artist_id == artist
        )

        if recent_same_artist < max_consecutive_same_artist:
            result.append(track)
            artist_counts[artist] = artist_counts.get(artist, 0) + 1

    return result
```

**Soft Diversity Scoring:**
```python
def calculate_artist_diversity_score(history, candidate):
    """
    Calculate diversity bonus based on artist distribution in history.
    Higher score if artist is underrepresented.
    """
    total_tracks = len(history)
    if total_tracks == 0:
        return 1.0  # No history, full bonus

    artist_count = sum(
        1 for t in history if t.artist_id == candidate.artist_id
    )

    # Expected frequency if perfectly uniform
    unique_artists = len(set(t.artist_id for t in history))
    expected_freq = 1.0 / max(unique_artists, 1)

    actual_freq = artist_count / total_tracks

    # Bonus if underrepresented, penalty if overrepresented
    if actual_freq < expected_freq:
        return 1.0 + (expected_freq - actual_freq) * 2
    else:
        return 1.0 / (1 + (actual_freq - expected_freq) * 2)
```

### Session-Based Filtering

Adjust scoring based on listening session context:

```python
def get_context_multiplier(context_type):
    """
    Adjust feature weights based on session context.
    """
    context_multipliers = {
        'workout': {
            'energy': 1.5,      # Prioritize high energy
            'tempo': 1.3,       # Prioritize faster tempo
            'valence': 1.1,     # Slightly favor positive
        },
        'focus': {
            'instrumentalness': 1.5,  # Prioritize instrumental
            'speechiness': 0.5,       # Deprioritize spoken word
            'energy': 0.8,            # Moderate energy
        },
        'chill': {
            'acousticness': 1.3,      # More acoustic
            'energy': 0.7,            # Lower energy
            'valence': 0.9,           # Neutral to positive
        },
        'party': {
            'danceability': 1.5,      # Highly danceable
            'valence': 1.3,           # Positive mood
            'energy': 1.2,            # High energy
        }
    }
    return context_multipliers.get(context_type, {})
```

---

## Implementation Recommendations

### Technology Stack

**Primary Stack (per planning docs):**
- **Language**: Python 3.10+
- **ML Library**: scikit-learn 1.0+
- **Data Manipulation**: pandas, numpy
- **Web Framework**: FastAPI
- **Database**: PostgreSQL

### Project Structure Recommendation

```
superior-spotify/
├── src/
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── similarity.py       # Cosine similarity functions
│   │   ├── scoring.py          # Smart shuffle scoring
│   │   ├── diversity.py        # MMR, diversity calculations
│   │   ├── profile.py          # User audio profile calculation
│   │   └── recommendations.py  # Recommendation pipeline
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── tracks.py
│   │   │   └── recommendations.py
│   └── core/
│       └── config.py
├── tests/
│   └── ml/
│       ├── test_similarity.py
│       └── test_scoring.py
├── requirements.txt
└── main.py
```

### Key Dependencies

**requirements.txt:**
```
# Web framework
fastapi>=0.100.0
uvicorn>=0.23.0

# Database
sqlalchemy>=2.0.0
asyncpg>=0.28.0

# ML & Data
scikit-learn>=1.3.0
numpy>=1.24.0
pandas>=2.0.0

# Spotify API
spotipy>=2.23.0

# Caching
redis>=4.6.0

# Background tasks
celery>=5.3.0
```

### Core ML Module Example

**src/ml/similarity.py:**
```python
"""Audio feature similarity calculations."""
from typing import List, Tuple, Dict
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Default audio feature weights for similarity
DEFAULT_FEATURE_WEIGHTS = np.array([
    1.2,  # danceability
    1.1,  # energy
    1.3,  # valence
    0.8,  # acousticness
    0.7,  # instrumentalness
    0.5,  # liveness
    0.6,  # speechiness
    1.0,  # tempo (normalized)
    0.5,  # loudness (normalized)
    0.8,  # mode
    0.7   # key (normalized)
])


def normalize_features(features: Dict[str, float]) -> np.ndarray:
    """
    Normalize raw Spotify audio features to 0-1 scale.

    Args:
        features: Raw audio features from Spotify API

    Returns:
        Normalized feature vector (11,)
    """
    return np.array([
        features['danceability'],
        features['energy'],
        features['valence'],
        features['acousticness'],
        features['instrumentalness'],
        features['liveness'],
        features['speechiness'],
        features['tempo'] / 200,  # Normalize: 0-200 BPM -> 0-1
        (features['loudness'] + 60) / 60,  # Normalize: -60 to 0 dB -> 0-1
        features['mode'],
        features['key'] / 11  # Normalize: 0-11 -> 0-1
    ])


def cosine_similarity_tracks(
    features_a: Dict[str, float],
    features_b: Dict[str, float],
    weights: np.ndarray = None
) -> float:
    """
    Calculate cosine similarity between two tracks' audio features.

    Args:
        features_a: Audio features for track A
        features_b: Audio features for track B
        weights: Optional feature weights

    Returns:
        Similarity score (0 to 1)
    """
    vec_a = normalize_features(features_a)
    vec_b = normalize_features(features_b)

    if weights is not None:
        vec_a = vec_a * weights
        vec_b = vec_b * weights

    return float(cosine_similarity(
        vec_a.reshape(1, -1),
        vec_b.reshape(1, -1)
    )[0][0])


def find_similar_tracks(
    target_features: Dict[str, float],
    candidate_features: List[Dict[str, float]],
    candidate_ids: List[str],
    n_results: int = 10
) -> List[Tuple[str, float]]:
    """
    Find the n most similar tracks to a target.

    Args:
        target_features: Target track audio features
        candidate_features: List of candidate track features
        candidate_ids: List of candidate track IDs
        n_results: Number of results to return

    Returns:
        List of (track_id, similarity) tuples
    """
    # Normalize all features
    target_vec = normalize_features(target_features).reshape(1, -1)
    candidate_vecs = np.array([
        normalize_features(f) for f in candidate_features
    ])

    # Calculate similarities
    similarities = cosine_similarity(target_vec, candidate_vecs)[0]

    # Get top n
    top_indices = similarities.argsort()[-n_results:][::-1]

    return [
        (candidate_ids[i], float(similarities[i]))
        for i in top_indices
    ]
```

**src/ml/scoring.py:**
```python
"""Smart shuffle scoring algorithm."""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import math

@dataclass
class TrackScoreComponents:
    """Individual score components for a track."""
    play_frequency: float
    audio_similarity: float
    diversity_bonus: float
    recency_bonus: float
    exploration_bonus: float
    total_score: float


class SmartShuffleScorer:
    """Calculate smart shuffle scores for tracks."""

    # Default weights (tunable)
    WEIGHT_PLAY_FREQUENCY = 0.35
    WEIGHT_AUDIO_SIMILARITY = 0.30
    WEIGHT_DIVERSITY = 0.20
    WEIGHT_RECENCY = 0.10
    WEIGHT_EXPLORATION = 0.05

    def __init__(
        self,
        user_profile: np.ndarray,
        recent_history: List['Track'],
        db_connection=None,
        current_time: datetime = None
    ):
        self.user_profile = user_profile
        self.recent_history = recent_history
        self.db = db_connection
        self.current_time = current_time or datetime.now()

    def calculate_score(self, track) -> TrackScoreComponents:
        """Calculate all score components for a track."""
        play_freq = self._play_frequency_score(track.id)
        audio_sim = self._audio_similarity(track)
        diversity = self._diversity_bonus(track)
        recency = self._recency_bonus(track)
        exploration = self._exploration_bonus(track.id)

        total = (
            self.WEIGHT_PLAY_FREQUENCY * play_freq +
            self.WEIGHT_AUDIO_SIMILARITY * audio_sim +
            self.WEIGHT_DIVERSITY * diversity +
            self.WEIGHT_RECENCY * recency +
            self.WEIGHT_EXPLORATION * exploration
        )

        return TrackScoreComponents(
            play_frequency=play_freq,
            audio_similarity=audio_sim,
            diversity_bonus=diversity,
            recency_bonus=recency,
            exploration_bonus=exploration,
            total_score=total
        )

    def _audio_similarity(self, track) -> float:
        """Calculate audio similarity to user profile."""
        from .similarity import normalize_features
        track_vec = normalize_features(track.audio_features)
        return float(cosine_similarity(
            track_vec.reshape(1, -1),
            self.user_profile.reshape(1, -1)
        )[0][0])

    def _play_frequency_score(self, track_id) -> float:
        """Calculate play frequency score."""
        if self.db is None:
            return 0.5  # Default if no data available

        # Query implementation as shown earlier
        # Returns normalized score 0-1
        pass

    def _diversity_bonus(self, track) -> float:
        """Calculate diversity bonus."""
        artist_penalty = sum(
            1 for t in self.recent_history
            if t.artist_id == track.artist_id
        )
        album_penalty = sum(
            0.5 for t in self.recent_history
            if t.album_id == track.album_id
        )
        return 1.0 / (1.0 + artist_penalty * 2.0 + album_penalty)

    def _recency_bonus(self, track) -> float:
        """Calculate recency bonus."""
        if track.last_played is None:
            return 1.0

        days = (self.current_time - track.last_played).days
        if days == 0:
            return 0.0
        return 1.0 - min(days / 30, 1.0)

    def _exploration_bonus(self, track_id) -> float:
        """Calculate exploration bonus."""
        if self.db is None:
            return 0.5

        # Query implementation as shown earlier
        pass
```

### Caching Strategy

Audio features are static - cache indefinitely:

```python
# Redis cache key pattern
AUDIO_FEATURES_KEY = "audio_features:{track_id}"
AUDIO_FEATURES_TTL = 0  # Permanent (features don't change)

TRACK_METADATA_KEY = "track_metadata:{track_id}"
TRACK_METADATA_TTL = 86400  # 24 hours

USER_PROFILE_KEY = "user_profile:{user_id}"
USER_PROFILE_TTL = 3600  # 1 hour (recalculated periodically)
```

### Performance Considerations

1. **Pre-compute user profiles**: Update hourly via Celery task
2. **Batch similarity calculations**: Use vectorized operations
3. **Cache scoring results**: For frequently accessed recommendations
4. **Limit candidate pool**: Score top 500-1000 candidates, not entire library

---

## Open Questions

### Unresolved Design Decisions

| Question | Options | Recommendation |
|----------|---------|----------------|
| **How to handle skipped tracks?** | Negative signal vs ignore | Treat as mild negative signal (reduce score) |
| **Window for user profile?** | 30/90/365 days | 90 days - balances recency with stability |
| **Diversity strictness?** | Hard limits vs soft scoring | Soft scoring (more flexible, tunable) |
| **Cold start for new users?** | Default profile vs random | Default profile based on general Spotify trends |
| **Track audio features latency?** | Sync vs async fetch | Sync on first access, cache thereafter |
| **Maximum playlist length?** | 50/100/200 tracks | 100 tracks - reasonable for shuffling |

### Metrics for Evaluation

Track these metrics to tune the algorithm:

1. **Skip Rate**: Lower is better (target < 15%)
2. **Completion Rate**: Higher is better (target > 70%)
3. **Repeat Listen Rate**: Measures satisfaction
4. **Discovery Rate**: New tracks per session (target 10-20%)
5. **Artist Diversity**: Unique artists per 50 tracks

### A/B Testing Framework

Recommend implementing configurable weight sets:

```python
WEIGHT_PRESETS = {
    'balanced': {
        'play_frequency': 0.35,
        'audio_similarity': 0.30,
        'diversity': 0.20,
        'recency': 0.10,
        'exploration': 0.05
    },
    'familiar': {
        'play_frequency': 0.50,
        'audio_similarity': 0.30,
        'diversity': 0.10,
        'recency': 0.05,
        'exploration': 0.05
    },
    'discover': {
        'play_frequency': 0.20,
        'audio_similarity': 0.25,
        'diversity': 0.25,
        'recency': 0.15,
        'exploration': 0.15
    }
}
```

---

## Appendix: Complete Smart Shuffle Flow

```python
def smart_shuffle_playlist(
    candidate_tracks: List[Track],
    user_id: str,
    num_tracks: int = 50,
    db_connection=None
) -> List[Track]:
    """
    Generate a smart-shuffled playlist from candidate tracks.

    This is the main entry point for smart shuffle.
    """
    # 1. Calculate user profile
    user_profile = calculate_user_audio_profile(user_id, db_connection)

    # 2. Get recent history for diversity
    recent_history = get_recent_plays(user_id, window_minutes=120)

    # 3. Initialize scorer
    scorer = SmartShuffleScorer(
        user_profile=user_profile,
        recent_history=recent_history,
        db_connection=db_connection
    )

    # 4. Score all candidates
    scored_tracks = []
    for track in candidate_tracks:
        components = scorer.calculate_score(track)
        scored_tracks.append((track, components.total_score))

    # 5. Re-rank with MMR for diversity
    mmr_ranked = mmr_re_rank(
        [t for t, s in sorted(scored_tracks, key=lambda x: x[1], reverse=True)],
        selected_tracks=[],
        lambda_param=0.7
    )

    # 6. Apply hard constraints (artist diversity)
    diversified = enforce_artist_diversity(mmr_ranked, max_consecutive_same_artist=1)

    # 7. Select top N with weighted sampling
    selected = []
    remaining = diversified[:100]  # Top 100 for sampling

    while len(selected) < num_tracks and remaining:
        # Create score dict for remaining
        scores = {t: next(s for _, s in scored_tracks if _ == t) for t in remaining}
        track_scores = [{'track': t, 'score': s} for t, s in scores.items()]

        # Weighted selection
        chosen = weighted_selection(track_scores, temperature=1.0)
        selected.append(chosen['track'])
        remaining = [t for t in remaining if t != chosen['track']]

    return selected
```

---

*Last updated: Based on planning documents dated 2024*
*Status: Design specification - ready for implementation*
