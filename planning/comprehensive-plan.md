# Superior Spotify - Comprehensive Product Plan

## Executive Summary

**Vision**: A "nerdy" Spotify-enhanced web app that brings intelligent ML-powered features, deep statistics, and social elements to your music listening experience.

**Core Problems We Solve**:
1. Spotify's shuffle algorithm doesn't respect personal preferences for variety, mood, or context
2. Limited visibility into listening patterns and audio feature preferences
3. Minimal social comparison and sharing of music taste statistics
4. No pattern-based automatic playlist generation

---

## What Spotify API Can & Cannot Do

### ✅ Available Through Spotify API

| Feature | Endpoint | Notes |
|---------|----------|-------|
| User profile | `GET /me` | Display name, country, premium status |
| Top artists/tracks | `GET /me/top/{type}` | Short/medium/long term windows |
| Recently played | `GET /me/player/recently-played` | **Only 20-50 tracks max** |
| Audio features | `GET /audio-features/{id}` | 11 key features per track |
| Track recommendations | `GET /recommendations` | Based on seed tracks/features |
| Playlists (CRUD) | Various | Create, read, modify playlists |
| Saved tracks library | GET/POST/DELETE | Your "liked songs" |
| Followed artists | GET /me/following | Artists you follow |
| Playback control | GET/POST /me/player | Play, pause, skip, seek |

### ❌ Critical Limitations

1. **No Full History**: Spotify only gives you 20-50 recently played tracks, NOT your complete listening history
2. **Premium Required**: Web API only works for Premium accounts
3. **Rate Limits**: Strict quotas on API calls (need aggressive caching)
4. **No Longitudinal Tracking**: Can't query "my top tracks from 2023"

### 🎯 Solution: Self-Tracking from Day One

**Critical Design Decision**: You MUST capture every play event as it happens and store it locally. This becomes your "listening history database" that Spotify API alone cannot provide.

---

## Audio Features Available (The Foundation for ML)

Spotify provides these features for every track (all normalized 0-1 except tempo/key):

| Feature | Meaning | Use Case |
|---------|---------|----------|
| **danceability** | Beat strength, rhythm stability | Party vs. chill modes |
| **energy** | Intensity, loudness, dynamics | Workout vs. relaxation |
| **valence** | Musical positiveness (happy→sad) | Mood matching |
| **acousticness** | Confidence track is acoustic | Electronic vs. acoustic |
| **instrumentalness** | Likelihood of no vocals | Focus/background music |
| **liveness** | Presence of audience | Live vs. studio feel |
| **speechiness** | Presence of spoken words | Rap vs. singing detection |
| **tempo** | BPM (not normalized) | Energy matching |
| **loudness** | dB (not normalized) | Volume normalization |
| **mode** | Major (1) vs Minor (0) | Mood indicator |
| **key** | Pitch class (0=C, 1=C#...) | Harmonic compatibility |

**Key Insight**: These features are your primary "embedding space" for similarity calculations, clustering, and personalized recommendations.

---

## ML Architecture for Superior Spotify

### Recommended Hybrid Approach

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT LAYER                              │
│  Listen events, skips, repeats, likes, playlist additions  │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
┌───────────────────────┐   ┌───────────────────────┐
│ COLLABORATIVE FILTER  │   │   CONTENT-BASED       │
│ - Item-item similarity│   │ - Audio feature sim   │
│ - Listening patterns  │   │ - MFCC/Chroma (opt)   │
└──────────┬────────────┘   └──────────┬────────────┘
           │                           │
           └───────────┬───────────────┘
                       ▼
          ┌─────────────────────────┐
          │   HYBRID SCORING        │
          │   - Weighted ensemble   │
          │   - Session context     │
          │   - Temporal factors    │
          └───────────┬─────────────┘
                      ▼
          ┌─────────────────────────┐
          │   DIVERSITY LAYER       │
          │   - MMR re-ranking      │
          │   - Artist/genre spread │
          │   - Recent history      │
          └───────────┬─────────────┘
                      ▼
          ┌─────────────────────────┐
          │   WEIGHTED SAMPLING     │
          │   - Softmax selection   │
          │   - Bandit exploration  │
          └─────────────────────────┘
```

### ML Techniques to Implement

#### 1. Content-Based Similarity (Easiest Starting Point)
- **Cosine similarity** on audio feature vectors
- Fast, explainable ("similar to X you liked")
- Works for cold-start (new songs immediately usable)

```python
# Conceptual implementation
from sklearn.metrics.pairwise import cosine_similarity

def find_similar_tracks(track_features, all_tracks, n=10):
    """Find tracks with similar audio profiles"""
    similarities = cosine_similarity([track_features], all_tracks)
    return top_n_tracks(similarities, n)
```

#### 2. Collaborative Filtering (Requires User Data)
- **Item-Item CF**: "Users who liked X also liked Y"
- **Matrix Factorization** (ALS, SVD): Latent factor models
- Better as user base grows and has more interaction data

#### 3. Smart Shuffle Algorithm
```python
def smart_shuffle_score(track, user_profile, recent_history):
    """
    Calculate weighted score for smart shuffle selection
    """
    score = (
        base_preference(track) * 0.4 +           # Frequency you've played it
        audio_similarity(track, user_profile) * 0.3 +  # Matches your taste
        diversity_bonus(track, recent_history) * 0.2 +  # Variety factor
        exploration_bonus(track) * 0.1            # Discover new stuff
    )
    return score
```

#### 4. Context/Mood Detection
- **Session-based clustering** on audio features
- Time-of-day patterns (morning vs evening preferences)
- Behavioral signals (skip rate, repeat rate)

---

## Database Schema (Core Focus)

### Core Tables

```sql
-- USERS
users:
  - id (UUID, PK)
  - spotify_id (VARCHAR, UNIQUE)
  - display_name (VARCHAR)
  - access_token (TEXT)
  - refresh_token (TEXT)
  - token_expires_at (TIMESTAMP)
  - created_at (TIMESTAMP)
  - last_active_at (TIMESTAMP)

-- LISTENING EVENTS (CRITICAL: Self-tracked history)
listening_events:
  - id (UUID, PK)
  - user_id (FK → users)
  - track_id (VARCHAR)
  - artist_id (VARCHAR)
  - played_at (TIMESTAMP)
  - duration_ms (INT)
  - position_ms (INT)  -- How far they listened
  - session_id (UUID)  -- Grouping for session analysis
  - device_type (VARCHAR)  -- phone, desktop, web, etc.

-- TRACKS (Cached metadata)
tracks:
  - id (VARCHAR, PK)  -- Spotify track ID
  - name (VARCHAR)
  - artist_id (VARCHAR)
  - artist_name (VARCHAR)
  - album_name (VARCHAR)
  - duration_ms (INT)
  - explicit (BOOLEAN)
  - popularity (INT)
  - fetched_at (TIMESTAMP)

-- AUDIO FEATURES (Cached, queried once per track)
audio_features:
  - track_id (VARCHAR, PK, FK → tracks)
  - acousticness (DECIMAL)
  - danceability (DECIMAL)
  - energy (DECIMAL)
  - valence (DECIMAL)
  - tempo (DECIMAL)
  - key (INT)
  - mode (INT)
  - loudness (DECIMAL)
  - instrumentalness (DECIMAL)
  - speechiness (DECIMAL)
  - liveness (DECIMAL)
  - duration_ms (INT)
  - time_signature (INT)
  - fetched_at (TIMESTAMP)

-- LISTENING SESSIONS (Grouped plays)
listening_sessions:
  - id (UUID, PK)
  - user_id (FK → users)
  - start_time (TIMESTAMP)
  - end_time (TIMESTAMP)
  - track_count (INT)
  - total_duration_ms (INT)
  - context_type (VARCHAR)  -- work, workout, chill, party, etc.
  - avg_valence (DECIMAL)   -- Mood indicator
  - avg_energy (DECIMAL)

-- USER PREFERENCES (Explicit weights)
user_preferences:
  - user_id (FK → users, PK)
  - preferred_danceability (DECIMAL)
  - preferred_energy (DECIMAL)
  - preferred_valence (DECIMAL)
  - preferred_acousticness (DECIMAL)
  - preferred_tempo_min (DECIMAL)
  - preferred_tempo_max (DECIMAL)
  - variety_weight (DECIMAL)  -- 0-1, how much variety to encourage
  - exploration_rate (DECIMAL)  -- Multi-armed bandit exploration

-- PLAYLISTS (User and system-generated)
playlists:
  - id (UUID, PK)
  - user_id (FK → users)
  - name (VARCHAR)
  - description (TEXT)
  - playlist_type (VARCHAR)  -- user, system, auto
  - criteria_json (JSONB)    -- For auto-playlists: mood, time, etc.
  - track_count (INT)
  - is_public (BOOLEAN)
  - spotify_playlist_id (VARCHAR)  -- Link to actual Spotify playlist
  - created_at (TIMESTAMP)
  - updated_at (TIMESTAMP)

-- PLAYLIST TRACKS
playlist_tracks:
  - playlist_id (FK → playlists, PK)
  - track_id (VARCHAR, PK)
  - position (INT)
  - added_at (TIMESTAMP)
  - added_by (VARCHAR)  -- user or system

-- USER STATS (Pre-computed aggregates)
user_stats:
  - id (UUID, PK)
  - user_id (FK → users)
  - stat_date (DATE)
  - stat_type (VARCHAR)  -- daily, weekly, monthly, all_time
  - total_plays (INT)
  - unique_tracks (INT)
  - unique_artists (INT)
  - unique_albums (INT)
  - avg_danceability (DECIMAL)
  - avg_energy (DECIMAL)
  - avg_valence (DECIMAL)
  - primary_genre (VARCHAR)
  - top_artist_ids (JSONB)
  - top_track_ids (JSONB)

-- FRIEND CONNECTIONS
friend_connections:
  - user_id (FK → users, PK)
  - friend_id (FK → users, PK)
  - relationship_type (VARCHAR)  -- following, blocked
  - created_at (TIMESTAMP)

-- FRIEND STATISTICS (For comparison features)
friend_stats:
  - id (UUID, PK)
  - user_id (FK → users)
  - friend_id (FK → users)
  - stat_date (DATE)
  - taste_similarity (DECIMAL)  -- Overall overlap score
  - artist_overlap (DECIMAL)
  - track_overlap (DECIMAL)
  - audio_profile_similarity (DECIMAL)
```

### Key Indexes for Performance

```sql
CREATE INDEX idx_listening_events_user_date ON listening_events(user_id, played_at DESC);
CREATE INDEX idx_listening_events_track ON listening_events(track_id);
CREATE INDEX idx_audio_features_cache ON audio_features(track_id);
CREATE INDEX idx_user_stats_user_date ON user_stats(user_id, stat_date DESC);
```

---

## Feature Specifications

### 1. Smart Shuffle Player

**How It Works**:
1. When user initiates "Smart Shuffle" on a playlist or library
2. Calculate preference scores for all candidate tracks
3. Apply diversity and exploration adjustments
4. Weighted random selection for next track
5. Track skips/replays to learn preferences

**Algorithm**:
```
score(track) = α × play_frequency + β × audio_similarity +
               γ × diversity_bonus - δ × recency_penalty

Where:
- play_frequency: How often user plays this track (0-1)
- audio_similarity: Cosine similarity to user's preferred profile
- diversity_bonus: Inverse of artist overlap with recent plays
- recency_penalty: Log decay based on last play time
- α, β, γ, δ: Tunable weights (start with balanced values)
```

**User Controls**:
- Variety slider (more familiar vs more exploration)
- Mood filters (high energy, chill, etc.)
- Artist diversity enforcement

### 2. Pattern-Based Playlists

**Auto-Generated Playlist Types**:

| Playlist | Criteria | Example |
|----------|----------|---------|
| "Morning Commute" | Time: 6-9am, moderate energy | Your typical morning tracks |
| "Evening Wind Down" | Time: 8-11pm, low valence | Relaxing evening music |
| "Workout Mix" | High energy, high tempo | Exercise favorites |
| "Focus Mode" | High instrumentalness, moderate energy | Study/work soundtrack |
| "Party Starter" | High danceability, high valence | Party playlist |
| "Deep Cuts" | Low play frequency, high preference score | Underplayed favorites |
| "Audio Twins" | Similar audio to top 10% but low play count | Discover similar tracks |

**Implementation**:
- Query listening events filtered by criteria
- Aggregate audio features per time/context bucket
- Select tracks matching dominant profile
- Exclude recently played (freshness)

### 3. Statistics Dashboard

**Metrics to Display**:

**Overview**:
- Total plays, hours streamed
- Unique tracks, artists, albums
- Favorite track, artist (all-time)

**Time-Based**:
- Top tracks/artists (7d, 30d, 90d, all-time)
- Listening streak (consecutive days)
- Plays per day/week/month

**Audio Profile**:
- Average danceability, energy, valence
- Audio feature distribution (histograms)
- Preferred tempo range
- Genre breakdown

**Behavioral**:
- Skip rate (tracks skipped within 30s)
- Repeat rate (tracks played multiple times)
- Discovery rate (new vs. familiar)
- Session patterns (when, how long)

**Visualizations**:
- Heatmap: Listening activity by hour/day
- Timeline: Audio feature trends over time
- Radar chart: Your audio profile vs. average
- Treemap: Genre distribution
- Line chart: Top artists over time

### 4. Social Features

**Friend Comparison**:
- Taste similarity score (0-100%)
- Artist overlap percentage
- Track overlap percentage
- Audio profile comparison (side-by-side radar)
- "Shared favorites" playlist (tracks both love)

**Leaderboards**:
- Most diverse taste (audio feature variance)
- Highest exploration rate (new tracks discovered)
- Longest listening streak
- Most variety in top 50

**Sharing**:
- Weekly stats card (shareable image)
- "My top 5 this week" with audio snippets
- Taste match percentage with friends

---

## Technical Stack Recommendations

### Backend
| Component | Choice | Why |
|-----------|--------|-----|
| Language | **Python** | Best ML ecosystem (sklearn, pandas) |
| Framework | **FastAPI** | Modern, async, great for APIs |
| Database | **PostgreSQL** | Relational, JSONB support for criteria |
| Cache | **Redis** | API response caching, session data |
| Queue | **Celery** | Background jobs (daily stats calc) |
| ORM | **SQLAlchemy** | Type-safe database layer |

### Frontend
| Component | Choice | Why |
|-----------|--------|-----|
| Framework | **Next.js (React)** or **Nuxt (Vue)** | Modern, SSR support |
| Charts | **Plotly** or **Chart.js** | Easy interactive charts |
| Styling | **Tailwind CSS** | Rapid UI development |
| State | **Zustand** or **Pinia** | Simple state management |

### ML Libraries
| Library | Use Case |
|---------|----------|
| **scikit-learn** | Cosine similarity, K-means, DBSCAN |
| **pandas** | Data manipulation, aggregation |
| **numpy** | Numerical operations |
| **implicit** | Matrix factorization (ALS) |
| **spotipy** | Spotify API client |

### Infrastructure
| Component | Choice | Why |
|-----------|--------|-----|
| Hosting | **Vercel** (frontend) + **Railway/Render** (backend) | Easy deployment |
| Database | **Supabase** or **Neon** | Managed PostgreSQL |
| Monitoring | **Sentry** | Error tracking |

---

## Development Phases

### Phase 1: Foundation (Weeks 1-3)
**Goals**: Core infrastructure and basic tracking

**Tasks**:
- [ ] Set up FastAPI backend with PostgreSQL
- [ ] Implement OAuth with Spotify
- [ ] Create database schema (users, tracks, audio_features, listening_events)
- [ ] Build listening event capture API (POST /listen)
- [ ] Implement audio feature caching
- [ ] Create basic user dashboard (top tracks/artists from self-tracked data)

**MVP Deliverable**: User can authenticate and see their self-tracked listening history

### Phase 2: Statistics & Visualization (Weeks 4-6)
**Goals**: Rich analytics and charts

**Tasks**:
- [ ] Build stats aggregation pipeline (daily/weekly/monthly)
- [ ] Create audio feature analysis endpoints
- [ ] Implement time-based pattern detection
- [ ] Build frontend dashboard with visualizations
- [ ] Add listening session grouping

**Deliverable**: Full statistics dashboard with charts and insights

### Phase 3: ML Features (Weeks 7-10)
**Goals**: Smart shuffle and recommendations

**Tasks**:
- [ ] Implement cosine similarity for track matching
- [ ] Build smart shuffle scoring algorithm
- [ ] Create pattern-based playlist generation
- [ ] Add mood/context detection
- [ ] Implement weighted random selection

**Deliverable**: Working smart shuffle and auto-playlists

### Phase 4: Social & Polish (Weeks 11-14)
**Goals**: Social features and refinement

**Tasks**:
- [ ] Build friend connection system
- [ ] Implement taste comparison features
- [ ] Create shareable stats cards
- [ ] Add leaderboards
- [ ] Performance optimization
- [ ] Mobile responsiveness

**Deliverable**: Full-featured social music analytics app

---

## Critical Design Decisions

### 1. Deployment Strategy

**Phase 1: Local Development**
- Single-user web app running on localhost
- Self-tracking via manual entry or browser integration
- Full statistics and visualization features

**Phase 2: Multi-User Deployment**
- Deploy to cloud (Railway, Render, or similar)
- User authentication with individual data isolation
- Social features enabled (friend connections, comparisons)

**Future: Mobile App**
- Can wrap web app as PWA (Progressive Web App)
- Or build native wrapper using Capacitor/Tauri

### 2. Playback Control Reality Check

**What's Possible via Spotify API**:
- `user-modify-playback-state`: Play, pause, skip, seek on user's active device
- Requires: Spotify Premium, user's active device must be available
- Limitation: Can't force playback if user isn't actively using Spotify

**Recommendation**: Focus on playlist generation + stats first
- Create smart playlists that users can play manually
- Playback control can be added later as "nice to have"

### 2. OAuth Scope Required

```
user-read-private          # User profile
user-read-email            # Email for account
user-read-recently-played  # Read Spotify history (limited)
playlist-read-private      # Read user playlists
playlist-modify-public     # Create public playlists
playlist-modify-private    # Create private playlists
user-library-modify        # Save/unsave tracks
user-modify-playback-state # Control playback
```

### 3. API Rate Limiting Strategy

- Cache audio features indefinitely (they don't change)
- Cache track metadata for 24 hours
- Batch API calls where possible (get several tracks at once)
- Use Redis for request deduplication

---

## Open Questions to Resolve

1. **Listening Capture Method**: How should we capture plays? Browser extension, bookmarklet, or desktop wrapper?

2. **Smart Shuffle Controls**: Should smart shuffle be a "mode" or generate static playlists?

3. **Social Privacy**: Default to private stats with opt-in sharing, or public by default?

4. **Monetization**: Free tier with basic stats, premium for advanced ML features?

5. **Mobile Support**: Progressive Web App (PWA) or native mobile apps?

---

## Resources & References

- [Spotify Web API Documentation](https://developer.spotify.com/documentation/web-api)
- [Spotify Audio Features](https://developer.spotify.com/documentation/web-api/reference/get-audio-features)
- [spotipy (Spotify Python Client)](https://github.com/plamere/spotipy)
- [scikit-learn Cosine Similarity](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise.cosine_similarity.html)
- [Last.fm API (for scrobbling comparison)](https://www.last.fm/api)

---

## Next Steps

1. **Choose tracking method** (browser extension vs. web wrapper)
2. **Set up project repository** with basic structure
3. **Implement OAuth flow** with Spotify
4. **Create initial database schema**
5. **Build MVP listening event capture**

Would you like me to dive deeper into any specific area before we start building?
