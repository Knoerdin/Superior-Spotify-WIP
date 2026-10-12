# Spotify API Integration Guide

Comprehensive documentation for all Spotify API interactions in Superior Spotify.

---

## What We Know from Planning Docs

### Spotify API Capabilities

The Spotify Web API provides access to:

- **User Profile**: Display name, country, premium status, email
- **Top Content**: User's top tracks and artists across three time windows (short/medium/long term)
- **Recently Played**: Limited history of tracks the user has played (20-50 tracks max)
- **Audio Features**: 11 normalized audio features for any track (danceability, energy, valence, etc.)
- **Track Recommendations**: Generate recommendations based on seed tracks or audio feature preferences
- **Playlists**: Full CRUD operations on user playlists (public and private)
- **Saved Tracks**: Access to user's "liked songs" library
- **Followed Artists**: List of artists the user follows
- **Playback Control**: Play, pause, skip, seek on user's active device

### Critical Capabilities Gaps

Spotify API does **NOT** provide:

1. **Complete Listening History**: Only the last 20-50 tracks are accessible via `recently_played`
2. **Historical Queries**: Cannot query "top tracks from 2023" or any time-beyond-recent history
3. **Free Tier Support**: Web API requires Premium accounts for playback control scopes
4. **Real-time Play Events**: No webhook or push notification for when a user plays a track

**Solution**: Self-tracking from day one is mandatory. Every play event must be captured and stored locally to build a complete listening history database.

---

## Sources

### Planning Documents Referenced

| Document | Path | Key Content |
|----------|------|-------------|
| Comprehensive Plan | `planning/comprehensive-plan.md` | Spotify API capabilities table, audio features, OAuth scopes |
| Architecture | `planning/architecture.md` | High-level API integration considerations |

### Spotify API Documentation

| Resource | URL |
|----------|-----|
| Web API Reference | https://developer.spotify.com/documentation/web-api |
| Audio Features | https://developer.spotify.com/documentation/web-api/reference/get-audio-features |
| OAuth Guide | https://developer.spotify.com/documentation/general/guides/authorization |
| spotipy (Python SDK) | https://github.com/plamere/spotipy |

---

## Available Endpoints

### Authentication & User Profile

| Endpoint | Method | Purpose | Notes |
|----------|--------|---------|-------|
| OAuth Authorization | GET | User consent flow | `client_id`, `redirect_uri`, `scope`, `state` params |
| Token Exchange | POST | Get access/refresh tokens | `/api/token` endpoint on Spotify auth servers |
| `/me` | GET | Current user profile | Premium status, country, display name |

### User Content

| Endpoint | Method | Purpose | Rate Limit Considerations |
|----------|--------|---------|---------------------------|
| `/me/top/tracks` | GET | User's top tracks | Three time ranges: `short_term`, `medium_term`, `long_term` |
| `/me/top/artists` | GET | User's top artists | Same time ranges as tracks |
| `/me/player/recently-played` | GET | Recently played (20-50 tracks) | **Hard limit of 50 per request** |
| `/me/player` | GET | Current playback state | May return 404 if nothing playing |
| `/me/tracks` | GET | Saved/liked songs | Pagination supported |

### Audio Features

| Endpoint | Method | Purpose | Limitations |
|----------|--------|---------|-------------|
| `/audio-features/{id}` | GET | Single track audio features | Can call individually or batch |
| `/audio-features` | GET | **Batch mode** - up to 50 track IDs | Use `ids` query param, comma-separated |

**Audio Features Returned** (all normalized 0-1 except tempo/key):
- `acousticness`, `danceability`, `energy`, `valence`
- `instrumentalness`, `liveness`, `speechiness`
- `tempo` (BPM), `loudness` (dB), `mode` (major/minor)
- `key` (pitch class), `duration_ms`, `time_signature`

### Recommendations & Playlists

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/recommendations` | GET | Generate recommendations from seed tracks/artists/genres |
| `/playlists` | POST | Create a new playlist |
| `/playlists/{id}/tracks` | POST | Add tracks to playlist |
| `/playlists/{id}/tracks` | GET | Get playlist contents |
| `/playlists/{id}` | PUT | Update playlist metadata |

### Playback Control

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/me/player/play` | PUT | Start playback |
| `/me/player/pause` | PUT | Pause playback |
| `/me/player/skip/next` | POST | Skip to next track |
| `/me/player/seek` | PUT | Seek to position |

---

## Critical Limitations

### The 20-50 Track History Gap

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| `recently_played` returns max 50 tracks | Cannot analyze long-term listening patterns from Spotify alone | **Must self-track every play** from day one |
| No historical API | Cannot backfill or import past history | History only accumulates forward from deployment |
| Gaps when app is offline | Missing plays during offline periods | Client should queue events for batch sync when online |

### Rate Limits

Spotify enforces strict API quotas. Key constraints:

- **Audio Features**: Batch endpoint limited to 50 track IDs per request
- **General Endpoints**: No published quotas, but aggressive caching is mandatory
- **Token Refresh**: Access tokens expire (typically 1 hour), must use refresh tokens

### Premium Account Requirement

| Feature | Free Account | Premium Account |
|---------|--------------|-----------------|
| Read top tracks/artists | Yes | Yes |
| Read recently played | Yes | Yes |
| Read audio features | Yes | Yes |
| Create playlists | Yes | Yes |
| Playback control | No | Yes |

**Recommendation**: Clearly communicate Premium requirement in onboarding. Playback control features are premium-only.

### Other Limitations

- **No Webhooks**: No server-to-server notifications for play events
- **No Bulk Export**: Must paginate through large datasets
- **Geographic Restrictions**: Some content unavailable in certain regions

---

## Rate Limiting Strategy

### Exponential Backoff with Retry

```python
async def api_call_with_retry(endpoint, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = await spotify_client.get(endpoint)
            return response
        except SpotifyException as e:
            if e.status_code == 429:  # Rate limited
                retry_after = int(e.headers.get('Retry-After', 1))
                await asyncio.sleep(retry_after * (2 ** attempt))
                continue
            elif e.status_code >= 500:
                await asyncio.sleep(1 * (2 ** attempt))
                continue
            raise
    raise MaxRetriesExceeded()
```

### Request Deduplication

Use Redis to prevent duplicate concurrent requests:

```python
async def get_audio_features_deduped(track_ids: list[str]) -> list[dict]:
    dedup_key = f"audio_features_lock:{hash(tuple(track_ids))}"
    
    # Try to acquire lock
    acquired = await redis_client.set(dedup_key, "1", nx=True, ex=10)
    if not acquired:
        # Wait for existing request to complete
        await asyncio.sleep(0.5)
        return await get_audio_features_cached(track_ids)
    
    try:
        return await get_audio_features_batch(track_ids)
    finally:
        await redis_client.delete(dedup_key)
```

### Rate Limit Bucket (Token Bucket Algorithm)

Implement a rate limiter that tracks request quotas:

- **Audio Features**: Max 50 IDs per request, chunk larger batches
- **General Endpoints**: Track requests per second, enforce soft limits

```python
class RateLimitBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate  # requests per second
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1
```

---

## Caching Patterns

### Cache Strategy by Data Type

| Data Type | Cache Duration | Storage | Rationale |
|-----------|----------------|---------|-----------|
| **Audio Features** | Indefinite (1 year) | Redis | Never change for a given track |
| **Track Metadata** | 24 hours | Redis | Album/artist info rarely changes |
| **User Profile** | 1 hour | Redis | Name/premium status stable |
| **Top Tracks/Artists** | 1-6 hours | Redis | Changes with listening habits |
| **Recently Played** | No cache (real-time) | N/A | Always fresh data needed |
| **Playlist Contents** | 1 hour | Redis | Users modify playlists occasionally |

### Implementation Pattern

```python
async def get_audio_features_cached(track_id: str) -> dict:
    """Audio features: cached indefinitely"""
    cache_key = f"audio_features:{track_id}"
    
    # Try cache first
    cached = await redis_client.get(cache_key)
    if cached:
        return cached
    
    # Fetch from API
    features = await spotify_client.audio_features([track_id])
    
    # Cache for 1 year (audio features never change)
    await redis_client.setex(cache_key, 31536000, features[0])
    
    return features[0]

async def get_track_metadata_cached(track_id: str) -> dict:
    """Track metadata: cached 24 hours"""
    cache_key = f"track:{track_id}"
    
    cached = await redis_client.get(cache_key)
    if cached:
        return cached
    
    track = await spotify_client.track(track_id)
    
    # Cache for 24 hours
    await redis_client.setex(cache_key, 86400, track)
    
    return track
```

### Batch Caching Optimization

For multiple tracks, use batch endpoint with combined caching:

```python
async def get_audio_features_batch(track_ids: list[str]) -> list[dict]:
    """
    Spotify limits audio-features batch to 50 IDs.
    Chunk larger requests and aggregate results.
    """
    results = {}
    
    for i in range(0, len(track_ids), 50):
        batch = track_ids[i:i+50]
        response = await spotify_client.audio_features(batch)
        for feat in response:
            if feat:  # May be None for unavailable tracks
                results[feat['id']] = feat
    
    return results
```

---

## Self-Tracking Requirement

### Why Self-Tracking Is Mandatory

Spotify's API limitations mean we cannot build the core features without capturing our own data:

| Feature | Requires Self-Tracking? | Reason |
|---------|------------------------|--------|
| Complete listening history | Yes | Spotify only provides 20-50 recent tracks |
| Year-in-review statistics | Yes | No historical query API exists |
| Long-term pattern detection | Yes | Patterns require weeks/months of data |
| "Top tracks from 2023" | Yes | Impossible via Spotify API alone |
| Skip rate analysis | Yes | Need to capture skip events |
| Repeat rate analysis | Yes | Need play frequency over time |

### Capture Events to Track

| Event Type | Data to Capture |
|------------|-----------------|
| **Track Play** | `track_id`, `artist_id`, `played_at`, `duration_ms`, `position_ms`, `session_id`, `device_type` |
| **Track Skip** | `track_id`, `position_ms`, `timestamp` |
| **Track Repeat** | `track_id`, `repeat_count`, `timestamps[]` |
| **Track Like** | `track_id`, `timestamp` |
| **Track Dislike** | `track_id`, `timestamp` |
| **Playlist Create** | `playlist_id`, `name`, `criteria`, `track_ids[]` |

### Listening Events Schema

```sql
CREATE TABLE listening_events (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    track_id VARCHAR NOT NULL,
    artist_id VARCHAR NOT NULL,
    played_at TIMESTAMP NOT NULL,
    duration_ms INTEGER,
    position_ms INTEGER,  -- How far user listened
    session_id UUID,      -- Groups plays into sessions
    device_type VARCHAR,  -- phone, desktop, web, mobile_app
    created_at TIMESTAMP DEFAULT NOW()
);

-- Critical indexes for query performance
CREATE INDEX idx_listening_events_user_date 
    ON listening_events(user_id, played_at DESC);
CREATE INDEX idx_listening_events_track 
    ON listening_events(track_id);
CREATE INDEX idx_listening_events_session 
    ON listening_events(session_id);
```

### Capture Methods

| Method | Pros | Cons | Recommended For |
|--------|------|------|-----------------|
| **Browser Extension** | Captures plays automatically, cross-platform | Requires user install, browser-only | Power users, desktop focus |
| **Bookmarklet** | Zero install, lightweight | Manual trigger, clunky UX | Early testing, minimal users |
| **Desktop Wrapper** | Full desktop integration | Requires Electron/Tauri app | Desktop-first users |
| **Mobile SDK** | Native mobile experience | Platform-specific, complex | Mobile-focused users |

**Recommendation for Phase 1**: Start with bookmarklet for minimal friction, evolve to browser extension for automatic capture.

---

## Open Questions

### Unresolved Integration Issues

| Question | Impact | Proposed Resolution |
|----------|--------|---------------------|
| **Capture method for MVP?** | Determines user experience and implementation complexity | Start with bookmarklet, iterate to browser extension |
| **Token refresh automation?** | If tokens expire mid-session, users lose functionality | Implement automatic refresh on 401, handle gracefully |
| **Offline play handling?** | Mobile users play offline; sync creates ordering issues | Queue events locally with timestamps, sync on reconnection |
| **Spotify playback state sync?** | Hard to know what user is playing without active integration | Use `player` endpoint polling + explicit events |
| **Handle unavailable tracks?** | Track IDs may become invalid (deleted/unavailable) | Gracefully skip, remove from analytics, log for cleanup |

### Potential API Improvements to Request

Spotify could improve their API for developers:

- Webhook notifications for play events
- Full history export/import endpoints
- Higher rate limits for authenticated users
- Bulk save/delete track operations

---

## Implementation Recommendations

### Service Layer Architecture

```
app/services/
├── spotify.py          # Spotify API client (existing)
├── tracking.py         # Listen event capture & persistence
├── audio_features.py   # Audio feature caching layer
├── recommendations.py  # Recommendation engine
└── rate_limiter.py     # Rate limiting & retry logic
```

### Recommended Implementation Order

**Phase 1: Foundation (Week 1)**
1. Implement OAuth flow and token storage
2. Build rate-limited API client with retry logic
3. Create listening event capture endpoint (`POST /listen`)
4. Implement audio feature caching (Redis)
5. Build basic track metadata caching

**Phase 2: Data Pipeline (Week 2-3)**
1. Create scheduled job to fetch recently played (if user active)
2. Implement batch audio feature fetching for historical tracks
3. Build session grouping logic (plays within X minutes)
4. Create user stats aggregation pipeline

**Phase 3: Features (Week 4+)**
1. Implement recommendation endpoint using `/recommendations`
2. Build smart shuffle scoring algorithm
3. Create pattern-based playlist generation
4. Add social features (friend comparisons)

### Key Code Patterns

#### Service Initialization

```python
# app/services/spotify.py (existing structure to extend)
class SpotifyService:
    def __init__(self):
        self.scopes = [
            "user-read-private",
            "user-read-email",
            "user-read-recently-played",
            "playlist-read-private",
            "playlist-modify-public",
            "playlist-modify-private",
            "user-library-modify",
            "user-modify-playback-state",
        ]
```

#### Error Handling Wrapper

```python
# Wrapper for all Spotify API calls
from spotipy import SpotifyException

class SpotifyAPIError(Exception):
    """Custom error for Spotify API failures"""
    pass

class UnauthorizedError(SpotifyAPIError):
    """Token expired or invalid"""
    pass

async def handle_spotify_error(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except SpotifyException as e:
            if e.status_code == 401:
                raise UnauthorizedError("Spotify token expired")
            elif e.status_code == 429:
                retry_after = int(e.headers.get('Retry-After', 1))
                raise RateLimitExceeded(retry_after)
            elif e.status_code >= 500:
                raise TemporaryServiceError("Spotify service unavailable")
            raise SpotifyAPIError(str(e))
    return wrapper
```

### Caching Key Naming Convention

Use consistent key naming for Redis cache:

```
{resource_type}:{identifier}:{scope}
```

Examples:
- `user_profile:{access_token_prefix}` - User profile cache
- `track:{track_id}` - Track metadata
- `audio_features:{track_id}` - Audio features (never expires)
- `top_tracks:{user_id}:{time_range}` - Top tracks cache
- `playlist:{playlist_id}` - Playlist contents

### Testing Recommendations

1. **Mock Spotify Client**: Use `pytest-mock` to mock spotipy responses
2. **Test Rate Limits**: Verify retry logic and backoff behavior
3. **Test Cache Behavior**: Ensure cache invalidation works correctly
4. **Test Edge Cases**: Handle unavailable tracks, missing audio features

---

## API Reference Quick Lookup

### OAuth Scopes Required

```
user-read-private          # User profile
user-read-email            # Email for account
user-read-recently-played  # Read recently played (limited)
playlist-read-private      # Read private playlists
playlist-modify-public     # Create public playlists
playlist-modify-private    # Create private playlists
user-library-modify        # Save/unsave tracks
user-modify-playback-state # Control playback (premium only)
```

### Audio Feature Ranges

| Feature | Range | Description |
|---------|-------|-------------|
| `danceability` | 0-1 | Higher = more danceable |
| `energy` | 0-1 | Higher = more intense/loud |
| `valence` | 0-1 | Higher = more positive/happy |
| `acousticness` | 0-1 | Higher = more acoustic |
| `instrumentalness` | 0-1 | Higher = more instrumental |
| `liveness` | 0-1 | Higher = live recording more likely |
| `speechiness` | 0-1 | Higher = more spoken words |
| `tempo` | 30-200 BPM | Not normalized |
| `loudness` | -60 to 0 dB | Not normalized |
| `mode` | 0 or 1 | Minor or Major |
| `key` | 0-11 | Pitch class (0=C) |

### Response Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 401 | Unauthorized | Refresh token, retry |
| 429 | Rate Limited | Respect `Retry-After` header |
| 500-503 | Service Error | Exponential backoff, retry |
| 404 | Not Found | Track unavailable, skip gracefully |

---

*Last updated: 2026-10-12*
*Maintained by: Superior Spotify Development Team*
