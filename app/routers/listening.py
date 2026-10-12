"""Listening event capture routes"""

import logging
from datetime import datetime
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from ..database import get_async_session
from ..models import User, ListeningEvent, Track, AudioFeatures

router = APIRouter(prefix="/listening", tags=["Listening Events"])
logger = logging.getLogger(__name__)


# Pydantic models for request/response
class ListeningEventCreate(BaseModel):
    """Request model for tracking a listen"""

    track_id: str = Field(..., description="Spotify track ID")
    artist_id: str = Field(..., description="Spotify artist ID")
    artist_name: Optional[str] = Field(None, description="Artist name")
    album_name: Optional[str] = Field(None, description="Album name")
    track_name: Optional[str] = Field(None, description="Track name")
    duration_ms: int = Field(..., ge=0, description="Track duration in ms")
    position_ms: Optional[int] = Field(0, ge=0, description="How far user listened")
    device_type: Optional[str] = Field("web", description="Device type")


class ListeningEventResponse(BaseModel):
    """Response model for tracking a listen"""

    success: bool
    event_id: str
    track_id: str
    played_at: str

    class Config:
        from_attributes = True


class TrackStats(BaseModel):
    """Track statistics for a user"""

    track_id: str
    track_name: str
    artist_name: str
    play_count: int
    total_duration_ms: int
    avg_position_ms: float


@router.post("/event", response_model=ListeningEventResponse, status_code=201)
async def capture_listen(
    event: ListeningEventCreate,
    user_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Capture a listening event (primary mechanism for building complete history)

    This endpoint is called whenever a user plays a track, allowing us to
    build a complete listening history beyond Spotify's 20-50 track limit.
    """
    try:
        # Get or create track
        track_statement = select(Track).where(Track.id == event.track_id)
        track_result = await session.execute(track_statement)
        track = track_result.scalar_one()

        if not track:
            # Create new track
            track = Track(
                id=event.track_id,
                name=event.track_name or f"Track {event.track_id}",
                artist_id=event.artist_id,
                artist_name=event.artist_name or "Unknown Artist",
                album_name=event.album_name or "",
                duration_ms=event.duration_ms,
                fetched_at=datetime.utcnow(),
            )
            session.add(track)
            await session.flush()

        # Create listening event
        event_id = uuid.uuid4()
        listening_event = ListeningEvent(
            id=event_id,
            user_id=uuid.UUID(user_id),
            track_id=event.track_id,
            artist_id=event.artist_id,
            played_at=datetime.utcnow(),
            duration_ms=event.duration_ms,
            position_ms=event.position_ms or 0,
            device_type=event.device_type or "web",
            session_id=None,  # TODO: Implement session grouping
        )
        session.add(listening_event)

        # Update user's last active time
        user_statement = select(User).where(User.id == uuid.UUID(user_id))
        user_result = await session.execute(user_statement)
        user = user_result.scalar_one()

        if user:
            user.last_active_at = datetime.utcnow()

        await session.commit()

        return ListeningEventResponse(
            success=True,
            event_id=str(event_id),
            track_id=event.track_id,
            played_at=datetime.utcnow().isoformat(),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid user_id: {e}")
    except Exception as e:
        logger.error(f"Error capturing listening event: {e}")
        raise HTTPException(status_code=500, detail="Failed to capture listening event")


@router.get("/history")
async def get_listening_history(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
):
    """Get user's listening history"""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id")

        # Get listening events with track info
    query = (
        select(ListeningEvent, Track, AudioFeatures)
        .join(Track, ListeningEvent.track_id == Track.id)
        .outerjoin(AudioFeatures, Track.id == AudioFeatures.track_id)
        .where(ListeningEvent.user_id == user_uuid)
        .order_by(desc(ListeningEvent.played_at))
        .limit(limit)
        .offset(offset)
    )

    result = await session.execute(query)
    rows = result.all()

    history = []
    for event, track, audio_features in rows:
        history.append(
            {
                "event_id": str(event.id),
                "played_at": event.played_at.isoformat(),
                "track": {
                    "id": track.id,
                    "name": track.name,
                    "artist_name": track.artist_name,
                    "album_name": track.album_name,
                    "duration_ms": track.duration_ms,
                },
                "audio_features": (
                    {
                        "danceability": audio_features.danceability,
                        "energy": audio_features.energy,
                        "valence": audio_features.valence,
                        "acousticness": audio_features.acousticness,
                        "tempo": audio_features.tempo,
                        "key": audio_features.key,
                        "mode": audio_features.mode,
                    }
                    if audio_features
                    else None
                ),
                "position_ms": event.position_ms,
                "device_type": event.device_type,
            }
        )

    return {"total": len(history), "limit": limit, "offset": offset, "items": history}


@router.get("/stats/top-tracks")
async def get_top_tracks(
    user_id: str,
    period: str = "all_time",  # day, week, month, year, all_time
    limit: int = 20,
    session: AsyncSession = Depends(get_async_session),
):
    """Get user's top tracks by play count"""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    # Build date filter based on period
    from sqlalchemy import text

    date_filter = None
    if period == "day":
        date_filter = func.date(ListeningEvent.played_at) == func.date(func.now())
    elif period == "week":
        date_filter = func.date(ListeningEvent.played_at) >= func.date(
            func.now() - 7
        )
    elif period == "month":
        date_filter = func.date(ListeningEvent.played_at) >= func.date(
            func.now() - 30
        )
    # For year and all_time, no filter needed

    # Query for top tracks
    if date_filter:
        query = (
            select(
                ListeningEvent.track_id,
                func.count().label("play_count"),
                func.sum(ListeningEvent.duration_ms).label("total_duration_ms"),
                func.avg(ListeningEvent.position_ms).label("avg_position_ms"),
            )
            .where(ListeningEvent.user_id == user_uuid)
            .where(date_filter)
            .group_by(ListeningEvent.track_id)
            .order_by(desc("play_count"))
            .limit(limit)
        )
    else:
        query = (
            select(
                ListeningEvent.track_id,
                func.count().label("play_count"),
                func.sum(ListeningEvent.duration_ms).label("total_duration_ms"),
                func.avg(ListeningEvent.position_ms).label("avg_position_ms"),
            )
            .where(ListeningEvent.user_id == user_uuid)
            .group_by(ListeningEvent.track_id)
            .order_by(desc("play_count"))
            .limit(limit)
        )

    result = await session.execute(query)
    stats = result.all()

    # Get track details for top tracks
    track_ids = [s.track_id for s in stats]
    tracks_statement = select(Track).where(Track.id.in_(track_ids))
    tracks_result = await session.execute(tracks_statement)
    tracks = {t.id: t for t in tracks_result.scalars().all()}

    top_tracks = []
    for s in stats:
        track = tracks.get(s.track_id)
        if track:
            top_tracks.append(
                {
                    "track_id": track.id,
                    "track_name": track.name,
                    "artist_name": track.artist_name,
                    "play_count": s.play_count,
                    "total_duration_ms": s.total_duration_ms,
                    "avg_position_ms": float(s.avg_position_ms) if s.avg_position_ms else 0,
                }
            )

    return {"period": period, "limit": limit, "items": top_tracks}
