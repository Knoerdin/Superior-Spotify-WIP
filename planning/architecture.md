# Superior Spotify - Planning Document

## Vision
A "nerdy" Spotify-enhanced web app that brings ML capabilities, deep statistics, and social features to Spotify. Focus on intelligent shuffle, pattern-based playlists, and comprehensive listening tracking.

## Core Problems to Solve
1. **Better Shuffle**: Spotify's random shuffle doesn't respect user preferences for variety, mood balance, or listening context
2. **Pattern-Based Playlists**: Auto-generate playlists based on listening patterns, time of day, mood detection
3. **Deep Statistics**: Track and visualize listening habits beyond what Spotify provides
4. **Social Features**: Share stats, compete with friends, discover through social connections

## Research in Progress
- [ ] Spotify API capabilities and limitations
- [ ] ML techniques for music recommendation
- [ ] Existing music analytics apps and gaps

---

## High-Level Architecture

### Data Flow
```
Spotify API → Our Backend → Database → ML Models → User Interface
     ↓              ↓            ↓           ↓          ↓
  Read/Write   ETL Pipeline  Analytics  Prediction  Visualization
```

### Key Components
1. **Authentication Layer**: OAuth with Spotify
2. **API Service**: Spotify API client with caching
3. **Data Pipeline**: Collect, normalize, store listening data
4. **Analytics Engine**: Calculate statistics, patterns, scores
5. **ML Service**: Recommendations, clustering, smart shuffle
6. **Social Layer**: Friends, sharing, leaderboards
7. **Frontend**: Dashboard, visualizations, controls

---

## Database Schema (Draft)

### Core Entities
- `users` - User profiles, Spotify tokens
- `listening_events` - Raw play history (track, timestamp, duration)
- `tracks` - Track metadata, audio features
- `playlists` - User and system-generated playlists
- `user_preferences` - Explicit likes/dislikes, weights
- `listening_sessions` - Grouped plays by context/time
- `friend_connections` - Social graph
- `stats_snapshots` - Aggregated daily/weekly/monthly stats

### Key Metrics to Track
- Play frequency per track/artist/album
- Time-based patterns (hour of day, day of week)
- Audio feature preferences (danceability, energy, valence, etc.)
- Skip rates, repeat rates
- Session contexts (morning, evening, workout, etc.)

---

## Feature Ideas

### Smart Shuffle
- Weighted random based on listening frequency + audio preferences
- "Similar to current mood" - find tracks matching current playlist's audio profile
- Variety control - ensure artist/album diversity
- Context-aware (workout, focus, chill modes)

### Pattern-Based Playlists
- "Your Evening Vibes" - based on 6-10pm listening patterns
- "Underplayed Gems" - tracks you love but rarely play
- "Audio Twins" - tracks similar to your most-played but you haven't heard
- "Mood Balancer" - auto-mix high/low energy for balanced listening

### Statistics
- Listen count, hours streamed
- Top N tracks, artists, albums (rolling windows)
- Audio feature distribution
- Discovery rate (new vs. familiar)
- Consistency scores (how predictable are your tastes)

### Social
- Friend comparison (top artists overlap)
- Weekly stats sharing
- "Taste match" percentage with friends
- Collaborative pattern playlists

---

## Spotify API Considerations

### What We Likely Need Access To
- **Reading**: Play history (limited), saved tracks, playlists, audio features
- **Writing**: Create playlists, modify playlists, save tracks, control playback
- **Authorization Scopes**: `user-read-private`, `user-read-recently-played`, `playlist-read-private`, `playlist-modify-public`, `playlist-modify-private`, `user-library-modify`, `user-modify-playback-state`

### Important Limitations
- Full listening history is NOT fully available through API (only recently played + limited history)
- Need to self-track to build complete history
- Rate limits apply (authentication required)

---

## Technical Considerations

### Backend
- Python recommended for ML ecosystem (scikit-learn, pandas, numpy)
- FastAPI or Django for API
- PostgreSQL for relational data, Redis for caching
- Celery for background jobs (daily stats calculation)

### Frontend
- React/Next.js or Vue/Nuxt for dashboard
- Chart.js, D3, or Plotly for visualizations
- Responsive mobile-first design

### ML Stack
- scikit-learn for clustering (KMeans, DBSCAN)
- Similarity metrics (cosine, Euclidean on audio features)
- Collaborative filtering for recommendations
- Weighted random sampling for shuffle

---

## Open Questions
1. How to handle the limitation of not having full Spotify history?
2. What's the minimum viable feature set?
3. Should we build a browser extension to track plays locally?
4. What privacy model do we want?
