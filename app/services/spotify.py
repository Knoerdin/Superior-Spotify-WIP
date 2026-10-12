"""Spotify API client service"""

import logging
from typing import Optional
import urllib.parse

import requests
import spotipy
from spotipy import SpotifyOAuth
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..config import get_settings
from ..models import User, Track, AudioFeatures
from .cache import redis_client

logger = logging.getLogger(__name__)
settings = get_settings()


class SpotifyService:
    """Service for interacting with Spotify API"""

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

    def get_auth_url(self, state: Optional[str] = None) -> str:
        """Get Spotify OAuth authorization URL"""
        auth = spotipy.SpotifyOAuth(
            client_id=settings.spotify_client_id,
            client_secret=settings.spotify_client_secret,
            redirect_uri=settings.spotify_redirect_uri,
            scope=" ".join(self.scopes),
            state=state,
        )
        return auth.get_authorize_url()

    def get_client(self, access_token: str) -> spotipy.Spotify:
        """Get authenticated Spotify client"""
        return spotipy.Spotify(auth=access_token)

    async def get_current_user(self, access_token: str) -> dict:
        """Get current user profile"""
        cache_key = f"user_profile:{access_token[:50]}"

        # Try cache first
        cached = await redis_client.get(cache_key)
        if cached:
            return cached

        client = self.get_client(access_token)
        user = client.current_user()

        # Cache for 1 hour
        await redis_client.setex(cache_key, 3600, user)

        return user

    async def get_user_top_tracks(
        self, access_token: str, time_range: str = "medium", limit: int = 20
    ) -> list[dict]:
        """Get user's top tracks"""
        client = self.get_client(access_token)
        return client.current_user_top_tracks(time_range=time_range, limit=limit)["items"]

    async def get_user_top_artists(
        self, access_token: str, time_range: str = "medium", limit: int = 20
    ) -> list[dict]:
        """Get user's top artists"""
        client = self.get_client(access_token)
        return client.current_user_top_artists(time_range=time_range, limit=limit)["items"]

    async def get_audio_features(self, track_ids: list[str]) -> list[dict]:
        """Get audio features for multiple tracks"""
        # Batch into chunks of 50 (Spotify API limit)
        results = []
        for i in range(0, len(track_ids), 50):
            batch = track_ids[i : i + 50]
            response = requests.get(
                "https://api.spotify.com/v1/audio-features",
                params={"ids": ",".join(batch)},
                headers={"Authorization": f"Bearer {await self._get_system_token()}"},
            )
            if response.status_code == 200:
                results.extend(response.json()["audio_features"])

        return results

    async def get_track_audio_features(self, track_id: str) -> Optional[dict]:
        """Get audio features for a single track with caching"""
        cache_key = f"audio_features:{track_id}"

        cached = await redis_client.get(cache_key)
        if cached:
            return cached

        client = self.get_client(await self._get_system_token())
        features = client.audio_features([track_id])[0]

        # Cache indefinitely (audio features don't change)
        await redis_client.setex(cache_key, 86400 * 365, features)

        return features

    async def get_track(self, track_id: str) -> Optional[dict]:
        """Get track metadata"""
        cache_key = f"track:{track_id}"

        cached = await redis_client.get(cache_key)
        if cached:
            return cached

        client = self.get_client(await self._get_system_token())
        track = client.track(track_id)

        # Cache for 24 hours
        await redis_client.setex(cache_key, 86400, track)

        return track

    async def _get_system_token(self) -> str:
        """Get a system-level access token for API calls"""
        # In production, use OAuth client_credentials flow
        # For now, we'll need to maintain a system token
        # This is a simplified version
        pass

    async def create_playlist(
        self,
        access_token: str,
        user_id: str,
        name: str,
        description: str = "",
        public: bool = False,
    ) -> dict:
        """Create a new playlist for a user"""
        client = self.get_client(access_token)
        return client.user_playlist_create(
            user=user_id, name=name, public=public, description=description
        )

    async def add_tracks_to_playlist(
        self, access_token: str, playlist_id: str, track_uris: list[str]
    ) -> dict:
        """Add tracks to a playlist"""
        client = self.get_client(access_token)
        return client.user_playlist_add_tracks(
            playlist_id=playlist_id, tracks=track_uris
        )

    async def get_recently_played(
        self, access_token: str, limit: int = 50
    ) -> list[dict]:
        """Get recently played tracks (max 50 from Spotify)"""
        client = self.get_client(access_token)
        return client.current_user_recently_played(limit=limit)["items"]


# Singleton instance
spotify_service = SpotifyService()
