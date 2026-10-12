# Project Structure for Superior Spotify

## Recommended Directory Layout

```
superior-spotify/
├── .env                          # Environment variables (DB URL, Spotify creds)
├── .gitignore
├── requirements.txt              # Python dependencies
├── README.md
│
├── app/                          # Main application
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Configuration loading
│   │
│   ├── database.py               # Database connection, session management
│   ├── models/                   # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── track.py
│   │   ├── listening_event.py
│   │   ├── audio_feature.py
│   │   ├── playlist.py
│   │   └── session.py
│   │
│   ├── routes/                   # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py              # OAuth with Spotify
│   │   ├── stats.py             # Statistics endpoints
│   │   ├── tracks.py            # Track management
│   │   ├── recommendations.py   # ML recommendations
│   │   └── playlists.py         # Playlist CRUD
│   │
│   ├── services/                 # Business logic
│   │   ├── __init__.py
│   │   ├── spotify_client.py    # Spotify API wrapper
│   │   ├── stats_calculator.py  # Aggregation logic
│   │   └── playlist_generator.py # Pattern-based playlists
│   │
│   └── schemas/                  # Pydantic models (request/response)
│       ├── __init__.py
│       ├── user.py
│       ├── track.py
│       └── stats.py
│
├── ml/                           # ML components
│   ├── __init__.py
│   ├── similarity.py            # Audio similarity calculations
│   ├── clustering.py            # Mood/session clustering
│   ├── shuffle.py               # Smart shuffle algorithm
│   ├── patterns.py              # Listening pattern analysis
│   └── recommendations.py       # Recommendation engine
│
├── utils/                        # Utility functions
│   ├── __init__.py
│   ├── time_utils.py            # Time parsing, session boundaries
│   └── audio_utils.py           # Audio feature normalization
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py              # pytest fixtures
│   ├── test_models.py
│   ├── test_similarity.py
│   └── test_recommendations.py
│
├── migrations/                   # Database migrations (Alembic)
│   └── versions/
│
├── frontend/                     # If using separate frontend later
│   ├── index.html
│   ├── css/
│   └── js/
│
└── scripts/                      # Utility scripts
    └── fetch_audio_features.py  # Batch fetch missing features
```

## Key File Contents (Starter Templates)

### app/main.py
```python
from fastapi import FastAPI
from app.routes import auth, stats, tracks, recommendations
from app.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Superior Spotify API")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(stats.router, prefix="/api/stats", tags=["statistics"])
app.include_router(tracks.router, prefix="/api/tracks", tags=["tracks"])
app.include_router(recommendations.router, prefix="/api/recommend", tags=["recommendations"])

@app.get("/")
def root():
    return {"message": "Superior Spotify API", "version": "0.1.0"}
```

### app/models/listening_event.py
```python
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ListeningEvent(Base):
    __tablename__ = "listening_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    track_id = Column(String, index=True, nullable=False)
    artist_id = Column(String, index=True)
    played_at = Column(DateTime, default=datetime.utcnow, index=True)
    duration_ms = Column(Integer)
    position_ms = Column(Integer)  # How far they listened
    session_id = Column(String)  # Grouping for session analysis

    __table_args__ = (
        # Composite index for common queries
        {"indexes": ["idx_user_played_at"]},
    )
```

### app/services/spotify_client.py
```python
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

class SpotifyClient:
    _instance = None

    def __init__(self):
        self.spotify = None

    def initialize(self, client_id: str, client_secret: str, redirect_uri: str):
        self.spotify = spotipy.SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope="user-read-private user-read-recently-played "
                  "playlist-read-private playlist-modify-public "
                  "playlist-modify-private user-library-modify"
        )

    @classmethod
    def get_instance(cls) -> "SpotifyClient":
        if cls._instance is None:
            cls._instance = SpotifyClient()
        return cls._instance

    def get_audio_features(self, track_id: str) -> Optional[Dict]:
        """Fetch audio features for a single track"""
        try:
            return self.spotify.audio_features(track_id)[0]
        except Exception as e:
            logger.error(f"Error fetching audio features: {e}")
            return None

    def get_tracks_audio_features(self, track_ids: List[str]) -> List[Dict]:
        """Batch fetch audio features (max 100 per request)"""
        all_features = []
        for i in range(0, len(track_ids), 100):
            batch = track_ids[i:i+100]
            features = self.spotify.audio_features(batch)
            all_features.extend(features)
        return all_features

    def get_recently_played(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get user's recently played tracks"""
        return self.spotify.current_user_recently_played(limit=limit)['items']
```

### ml/similarity.py
```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple

class AudioSimilarity:
    """Audio feature similarity calculations for track matching"""

    FEATURE_WEIGHTS = {
        'danceability': 0.15,
        'energy': 0.15,
        'valence': 0.20,  # Mood is important
        'acousticness': 0.10,
        'instrumentalness': 0.10,
        'tempo': 0.15,
        'loudness': 0.10,
    }

    def __init__(self, audio_features_db):
        """Initialize with database connection for audio features"""
        self.db = audio_features_db
        self.feature_cols = list(self.FEATURE_WEIGHTS.keys())

    def get_track_vector(self, track_id: str) -> np.ndarray:
        """Get weighted audio feature vector for a track"""
        features = self.db.get_features(track_id, self.feature_cols)
        vector = np.array([features.get(col, 0) for col in self.feature_cols])
        return vector

    def cosine_similarity_tracks(self, track_id: str, candidate_ids: List[str]) -> List[Tuple[str, float]]:
        """Calculate cosine similarity between track and candidates"""
        target_vec = self.get_track_vector(track_id).reshape(1, -1)
        candidate_vecs = np.array([
            self.get_track_vector(tid) for tid in candidate_ids
        ])

        similarities = cosine_similarity(target_vec, candidate_vecs)[0]
        return [(track_ids[i], similarities[i]) for i in range(len(track_ids))]

    def find_similar_tracks(self, track_id: str, limit: int = 10) -> List[Dict]:
        """Find most similar tracks to a given track"""
        # Get all candidate tracks from user's library/history
        candidate_ids = self.db.get_user_track_ids()

        similarities = self.cosine_similarity_tracks(track_id, candidate_ids)
        similarities.sort(key=lambda x: x[1], reverse=True)

        similar_ids = [tid for tid, _ in similarities[:limit]]
        return self.db.get_tracks(similar_ids)
```

### app/routes/stats.py
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.stats_calculator import StatsCalculator
from app.schemas.stats import StatsResponse, TopItemsResponse

router = APIRouter()

@router.get("/overview", response_model=StatsResponse)
def get_overview(db: Session = Depends(get_db), user_id: str = "current_user"):
    """Get overall listening statistics"""
    calculator = StatsCalculator(db)
    return calculator.get_overview_stats(user_id)

@router.get("/top-tracks", response_model=TopItemsResponse)
def get_top_tracks(
    db: Session = Depends(get_db),
    user_id: str = "current_user",
    limit: int = 10,
    time_range: str = "all_time"
):
    """Get top tracks for user"""
    calculator = StatsCalculator(db)
    return calculator.get_top_tracks(user_id, limit, time_range)

@router.get("/audio-profile")
def get_audio_profile(
    db: Session = Depends(get_db),
    user_id: str = "current_user"
):
    """Get user's average audio feature profile"""
    calculator = StatsCalculator(db)
    return calculator.get_audio_profile(user_id)
```

### app/services/stats_calculator.py
```python
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models.listening_event import ListeningEvent
from app.models.audio_feature import AudioFeature
from datetime import datetime, timedelta
from typing import Dict, List

class StatsCalculator:
    def __init__(self, db: Session):
        self.db = db

    def get_overview_stats(self, user_id: str) -> Dict:
        """Calculate overall listening statistics"""
        events = self.db.query(ListeningEvent).filter(
            ListeningEvent.user_id == user_id
        )

        total_plays = events.count()
        unique_tracks = events.values(ListeningEvent.track_id).distinct().count()
        unique_artists = events.values(ListeningEvent.artist_id).distinct().count()

        # Calculate average audio features
        track_ids = [e.track_id for e in events]
        audio_features = self.db.query(AudioFeature).filter(
            AudioFeature.track_id.in_(track_ids)
        )

        avg_danceability = audio_features.with_entities(
            func.avg(AudioFeature.danceability)
        ).scalar()

        return {
            "total_plays": total_plays,
            "unique_tracks": unique_tracks,
            "unique_artists": unique_artists,
            "avg_danceability": avg_danceability or 0,
            # ... more stats
        }

    def get_top_tracks(self, user_id: str, limit: int, time_range: str) -> List[Dict]:
        """Get top played tracks with audio features"""
        # Implementation for top tracks calculation
        pass
```

---

## Environment Variables (.env)

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/superior_spotify

# Spotify API Credentials
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8000/callback

# App Settings
SECRET_KEY=your_secret_key_for_oauth
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## Package Dependencies (requirements.txt)

```txt
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.13.0

# Spotify API
spotipy==2.23.0

# Data & ML
pandas==2.1.3
numpy==1.26.2
scikit-learn==1.3.2

# Charts & Visualization
plotly==5.18.0
streamlit==1.28.2  # For rapid MVP frontend

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Background Tasks
celery==5.3.4
redis==5.0.1

# Utilities
python-dotenv==1.0.0
pydantic==2.5.2
httpx==0.25.2

# Testing
pytest==7.4.3
pytest-cov==4.1.0
```

---

## Next Steps to Start Building

1. **Set up the project structure** - Create the directories above
2. **Initialize database** - Run PostgreSQL locally via Docker
3. **Create models** - Implement SQLAlchemy models
4. **Build Spotify client** - Set up OAuth and API wrapper
5. **Create Streamlit MVP** - Quick frontend for stats visualization
6. **Implement ML features** - Similarity, clustering, smart shuffle

Would you like me to start setting up the actual project structure with these files?
