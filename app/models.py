"""Database models using SQLAlchemy"""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base model class with common functionality"""

    def to_dict(self):
        """Convert model to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# Users table
class User(Base):
    """User profiles and OAuth tokens"""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )
    spotify_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    country: Mapped[str] = mapped_column(String(2), nullable=True)

    # OAuth tokens
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    timestamps: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    listening_events: Mapped[list["ListeningEvent"]] = relationship(
        back_populates="user"
    )
    listening_sessions: Mapped[list["ListeningSession"]] = relationship(
        back_populates="user"
    )
    user_preferences: Mapped["UserPreferences"] = relationship(
        back_populates="user", uselist=False
    )
    playlists: Mapped[list["Playlist"]] = relationship(back_populates="user")
    saved_stats: Mapped[list["UserStats"]] = relationship(back_populates="user")


# Listening Events - CRITICAL for self-tracking
class ListeningEvent(Base):
    """Self-tracked listening history (critical - Spotify only gives 20-50 recent plays)"""

    __tablename__ = "listening_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("users.id"), nullable=False, index=True
    )
    track_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    artist_id: Mapped[str] = mapped_column(String(100), nullable=False)
    played_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True
    )
    duration_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)
    position_ms: Mapped[int] = mapped_column(BigInteger, default=0)  # How far they listened
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID, nullable=True)
    device_type: Mapped[str] = mapped_column(String(50), nullable=True, default="web")

    # Relationships
    user: Mapped[User] = relationship(back_populates="listening_events")
    track: Mapped["Track"] = relationship(back_populates="listening_events")

    __table_args__ = (
        UniqueConstraint("user_id", "played_at", name="uq_user_played_at"),
    )


# Tracks - Cached metadata from Spotify
class Track(Base):
    """Cached track metadata from Spotify"""

    __tablename__ = "tracks"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)  # Spotify track ID
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    artist_id: Mapped[str] = mapped_column(String(100), nullable=False)
    artist_name: Mapped[str] = mapped_column(String(255), nullable=False)
    album_name: Mapped[str] = mapped_column(String(255), nullable=True)
    duration_ms: Mapped[int] = mapped_column(BigInteger, nullable=True)
    explicit: Mapped[bool] = mapped_column(Boolean, default=False)
    popularity: Mapped[int] = mapped_column(Integer, nullable=True)

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    audio_features: Mapped["AudioFeatures"] = relationship(
        back_populates="track", uselist=False
    )
    listening_events: Mapped[list["ListeningEvent"]] = relationship(back_populates="track")


# Audio Features - Cached from Spotify API
class AudioFeatures(Base):
    """Cached audio features per track (fetched once, stored indefinitely)"""

    __tablename__ = "audio_features"

    track_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("tracks.id"), primary_key=True
    )
    acousticness: Mapped[float] = mapped_column(Float, default=0.0)
    danceability: Mapped[float] = mapped_column(Float, default=0.0)
    energy: Mapped[float] = mapped_column(Float, default=0.0)
    valence: Mapped[float] = mapped_column(Float, default=0.0)
    tempo: Mapped[float] = mapped_column(Float, default=0.0)
    key: Mapped[int] = mapped_column(Integer, nullable=True)
    mode: Mapped[int] = mapped_column(Integer, nullable=True)
    loudness: Mapped[float] = mapped_column(Float, default=0.0)
    instrumentalness: Mapped[float] = mapped_column(Float, default=0.0)
    speechiness: Mapped[float] = mapped_column(Float, default=0.0)
    liveness: Mapped[float] = mapped_column(Float, default=0.0)
    duration_ms: Mapped[int] = mapped_column(BigInteger, nullable=True)
    time_signature: Mapped[int] = mapped_column(Integer, nullable=True)

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationship
    track: Mapped[Track] = relationship(back_populates="audio_features")


# Listening Sessions - Grouped plays
class ListeningSession(Base):
    """Grouped listening sessions by context"""

    __tablename__ = "listening_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("users.id"), nullable=False
    )
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    track_count: Mapped[int] = mapped_column(Integer, default=0)
    total_duration_ms: Mapped[int] = mapped_column(BigInteger, default=0)
    context_type: Mapped[str] = mapped_column(String(50), nullable=True)  # work, workout, chill, party
    avg_valence: Mapped[float] = mapped_column(Float, nullable=True)  # Mood indicator
    avg_energy: Mapped[float] = mapped_column(Float, nullable=True)

    # Relationships
    user: Mapped[User] = relationship(back_populates="listening_sessions")


# User Preferences - Explicit weights for recommendations
class UserPreferences(Base):
    """User preferences for smart shuffle algorithm"""

    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("users.id"), primary_key=True
    )

    # Audio feature preferences
    preferred_danceability: Mapped[float] = mapped_column(Float, default=0.5)
    preferred_energy: Mapped[float] = mapped_column(Float, default=0.5)
    preferred_valence: Mapped[float] = mapped_column(Float, default=0.5)
    preferred_acousticness: Mapped[float] = mapped_column(Float, default=0.5)
    preferred_tempo_min: Mapped[float] = mapped_column(Float, default=60.0)
    preferred_tempo_max: Mapped[float] = mapped_column(Float, default=180.0)

    # Algorithm weights
    variety_weight: Mapped[float] = mapped_column(Float, default=0.5)  # 0-1
    exploration_rate: Mapped[float] = mapped_column(Float, default=0.1)  # Multi-armed bandit

    # Relationships
    user: Mapped[User] = relationship(back_populates="user_preferences")


# Playlists
class Playlist(Base):
    """User and system-generated playlists"""

    __tablename__ = "playlists"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    playlist_type: Mapped[str] = mapped_column(
        String(20), default="user"
    )  # user, system, auto
    criteria_json: Mapped[dict] = mapped_column(JSONB, nullable=True)  # For auto-playlists
    track_count: Mapped[int] = mapped_column(Integer, default=0)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    spotify_playlist_id: Mapped[str] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user: Mapped[User] = relationship(back_populates="playlists")
    tracks: Mapped[list["PlaylistTrack"]] = relationship(
        back_populates="playlist", cascade="all, delete-orphan"
    )


class PlaylistTrack(Base):
    """Playlist tracks mapping"""

    __tablename__ = "playlist_tracks"

    playlist_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("playlists.id"), primary_key=True
    )
    track_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    added_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    added_by: Mapped[str] = mapped_column(String(50), default="user")  # user or system

    # Relationships
    playlist: Mapped[Playlist] = relationship(back_populates="tracks")


# User Stats - Pre-computed aggregates
class UserStats(Base):
    """Pre-computed user statistics"""

    __tablename__ = "user_stats"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("users.id"), nullable=False
    )
    stat_date: Mapped[Date] = mapped_column(Date, nullable=False)
    stat_type: Mapped[str] = mapped_column(String(20), nullable=False)  # daily, weekly, monthly, all_time

    # Core metrics
    total_plays: Mapped[int] = mapped_column(BigInteger, default=0)
    unique_tracks: Mapped[int] = mapped_column(Integer, default=0)
    unique_artists: Mapped[int] = mapped_column(Integer, default=0)
    unique_albums: Mapped[int] = mapped_column(Integer, default=0)

    # Audio profile
    avg_danceability: Mapped[float] = mapped_column(Float, default=0.0)
    avg_energy: Mapped[float] = mapped_column(Float, default=0.0)
    avg_valence: Mapped[float] = mapped_column(Float, default=0.0)

    # Top content
    primary_genre: Mapped[str] = mapped_column(String(100), nullable=True)
    top_artist_ids: Mapped[list] = mapped_column(JSONB, default=list)
    top_track_ids: Mapped[list] = mapped_column(JSONB, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    user: Mapped[User] = relationship(back_populates="saved_stats")

    __table_args__ = (UniqueConstraint("user_id", "stat_date", "stat_type", name="uq_user_stat"),)


# Create indexes for performance
__all__ = [
    "User",
    "ListeningEvent",
    "Track",
    "AudioFeatures",
    "ListeningSession",
    "UserPreferences",
    "Playlist",
    "PlaylistTrack",
    "UserStats",
]
