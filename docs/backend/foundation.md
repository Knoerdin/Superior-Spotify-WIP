# Backend Foundation Documentation

**Last Updated:** October 2026

Comprehensive guidance for building the Superior Spotify backend infrastructure.

---

## What We Know from Planning Docs

### Core Requirements

From `planning/comprehensive-plan.md` and `planning/architecture.md`:

| Area | Requirement |
|------|-------------|
| **Framework** | FastAPI with async support |
| **Database** | PostgreSQL with SQLAlchemy ORM |
| **Cache** | Redis for API responses and session data |
| **API Style** | RESTful endpoints with JSON responses |
| **Auth** | OAuth 2.0 with JWT for session management |

### Database Schema (from planning)

**Core Tables Required:**

| Table | Purpose | Critical Fields |
|-------|---------|-----------------|
| `users` | User profiles and OAuth tokens | spotify_id, access_token, refresh_token |
| `listening_events` | Self-tracked play history | user_id, track_id, played_at, position_ms |
| `tracks` | Cached Spotify track metadata | id, name, artist_id, artist_name |
| `audio_features` | Cached audio features | track_id, danceability, energy, valence, tempo |
| `listening_sessions` | Grouped plays by context | user_id, start_time, avg_valence |
| `user_preferences` | ML preference weights | preferred_danceability, variety_weight |
| `playlists` | User and auto-generated playlists | name, criteria_json, spotify_playlist_id |
| `user_stats` | Pre-computed aggregates | total_plays, unique_tracks, avg_valence |

### API Endpoints Required (Phase 1)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/login` | GET | Redirect to Spotify OAuth |
| `/auth/callback` | GET | Handle OAuth callback |
| `/listening/event` | POST | Capture a listening event |
| `/listening/history` | GET | Get user's listening history |
| `/listening/stats/top-tracks` | GET | Get top tracks by period |

---

## Sources

### Planning Documents Referenced

| Document | Path | Key Content |
|----------|------|-------------|
| Comprehensive Plan | `planning/comprehensive-plan.md` | Database schema, feature specs |
| Architecture | `planning/architecture.md` | High-level system design |
| Tech Stack | `planning/tech-stack.md` | Technology recommendations |
| Project Structure | `planning/project-structure.md` | Directory layout |

### Existing Code Files

| File | Path | Purpose |
|------|------|---------|
| Models | `app/models.py` | SQLAlchemy model definitions |
| Config | `app/config.py` | Settings and environment variables |
| Database | `app/database.py` | Connection and session management |
| Main App | `app/main.py` | FastAPI application |
| Auth Router | `app/routers/auth.py` | OAuth endpoints |
| Listening Router | `app/routers/listening.py` | Event capture endpoints |
| Spotify Service | `app/services/spotify.py` | Spotify API client |
| Cache Service | `app/services/cache.py` | Redis caching layer |

---

## FastAPI Best Practices

### Application Structure

```
app/
├── __init__.py
├── main.py                 # FastAPI app creation
├── config.py               # Settings management
├── database.py             # DB connection
├── models.py               # SQLAlchemy models
├── routers/
│   ├── __init__.py
│   ├── auth.py             # OAuth routes
│   ├── listening.py        # Event capture routes
│   ├── dashboard.py        # Stats and analytics
│   └── health.py           # Health checks
└── services/
    ├── __init__.py
    ├── spotify.py          # Spotify API client
    ├── cache.py            # Redis cache
    └── auth.py             # JWT auth
```

### Dependency Injection Pattern

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_async_session
from .models import User

async def get_current_user(
    session: AsyncSession = Depends(get_async_session)
) -> User:
    """Get current authenticated user from token"""
    # Extract token from header
    # Decode JWT
    # Return user or raise 401
    pass

@router.get("/listening/history")
async def get_history(
    user: User = Depends(get_current_user),  # Authenticated user
    session: AsyncSession = Depends(get_async_session),
    limit: int = 50
):
    """Endpoint that requires authentication"""
    # user.id is now available from authenticated context
    pass
```

### Async Database Session

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### Error Handling

```python
from fastapi import HTTPException

class AppException(Exception):
    """Base application exception"""
    status_code = 500
    detail = "An error occurred"

class NotFoundError(AppException):
    status_code = 404
    detail = "Resource not found"

class UnauthorizedError(AppException):
    status_code = 401
    detail = "Unauthorized"

# Usage in endpoints
async def get_track(track_id: str, session: AsyncSession):
    track = await session.get(Track, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track
```

---

## SQLAlchemy ORM Best Practices

### Model Definition Pattern

```python
from sqlalchemy import Column, DateTime, String, Integer
from sqlalchemy.orm import DeclarativeBase
import uuid

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    spotify_id = Column(String(100), unique=True, index=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

### Query Pattern

```python
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# Single record
async def get_user_by_spotify_id(session: AsyncSession, spotify_id: str) -> User:
    statement = select(User).where(User.spotify_id == spotify_id)
    result = await session.execute(statement)
    return result.scalar_one()

# Multiple records with pagination
async def get_listening_events(
    session: AsyncSession,
    user_id: str,
    limit: int = 50,
    offset: int = 0
) -> list[ListeningEvent]:
    statement = (
        select(ListeningEvent)
        .where(ListeningEvent.user_id == user_id)
        .order_by(ListeningEvent.played_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(statement)
    return result.scalars().all()

# Aggregation
async def get_user_play_count(session: AsyncSession, user_id: str) -> int:
    statement = select(func.count()).select_from(ListeningEvent).where(
        ListeningEvent.user_id == user_id
    )
    result = await session.execute(statement)
    return result.scalar()
```

---

## Database Indexes

**Critical indexes for performance:**

```sql
-- Listening events (most queried table)
CREATE INDEX idx_listening_events_user_date 
    ON listening_events(user_id, played_at DESC);
CREATE INDEX idx_listening_events_track 
    ON listening_events(track_id);
CREATE INDEX idx_listening_events_session 
    ON listening_events(session_id);

-- Audio features (lookups by track_id)
CREATE INDEX idx_audio_features_cache 
    ON audio_features(track_id);

-- User stats (queries by user and date)
CREATE INDEX idx_user_stats_user_date 
    ON user_stats(user_id, stat_date DESC);
```

---

## Open Questions

| Question | Impact | Proposed Resolution |
|----------|--------|---------------------|
| JWT vs Session auth? | Affects auth middleware design | Use JWT for API, HTTP-only cookies for web |
| PostgreSQL connection pool size? | Performance under load | Start with 10, monitor and scale |
| Migration strategy for production? | Zero-downtime deploys | Use Alembic with careful migration design |
| Background task handling? | Async feature for stats calc | Start with simple cron, consider Celery later |

---

## Implementation Recommendations

### Priority 1: Foundation (Week 1)

1. **Database Setup**
   - Docker Compose for local PostgreSQL + Redis
   - Alembic for migrations
   - Connection pooling configuration

2. **Authentication Layer**
   - JWT service with proper expiration
   - Auth middleware to extract user from token
   - OAuth flow completion

3. **API Endpoints**
   - Listening event capture (`POST /listening/event`)
   - History retrieval (`GET /listening/history`)
   - Health checks (`GET /health`, `GET /health/db`, `GET /health/redis`)

### Priority 2: Data Layer (Week 2)

1. **Stats Aggregation**
   - Top tracks by period
   - User audio profile calculation
   - Listening session grouping

2. **Caching Layer**
   - Audio features cache (indefinite)
   - Track metadata cache (24h)
   - User profile cache (1h)

### Priority 3: Integration (Week 3)

1. **Spotify Integration**
   - Audio feature fetching
   - Playlist creation
   - Playback control (optional)

---

## Running the Backend

```bash
# Start infrastructure
docker-compose up -d

# Set up Python environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Spotify credentials

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access docs
# http://localhost:8000/docs
```

---

## Testing Guidelines

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
async def test_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_capture_listen_event(test_client, test_user):
    response = await test_client.post(
        "/listening/event",
        json={
            "track_id": "test_track_id",
            "artist_id": "test_artist_id",
            "duration_ms": 180000,
            "user_id": str(test_user.id)
        },
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["track_id"] == "test_track_id"
```

---

*Last updated: 2026-10-12*
*Maintained by: Superior Spotify Development Team*
