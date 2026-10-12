"""OAuth authentication routes"""

import logging
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from ..database import get_async_session
from ..models import User
from ..services.spotify import spotify_service
from ..config import get_settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()
logger = logging.getLogger(__name__)


@router.get("/login")
async def login():
    """Redirect to Spotify OAuth login"""
    auth_url = spotify_service.get_auth_url()
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(
    request: Request,
    code: Optional[str] = None,
    error: Optional[str] = None,
    session: AsyncSession = Depends(get_async_session),
):
    """Handle Spotify OAuth callback"""

    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    # Exchange code for tokens
    auth = spotify_service.get_client("")  # Empty token for initial exchange

    # Use spotipy to get tokens
    sp = spotify_service
    auth_manager = sp.get_auth_manager(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        redirect_uri=settings.spotify_redirect_uri,
    )

    try:
        token_info = auth_manager.get_access_token(code)
        access_token = token_info["access_token"]
        refresh_token = token_info.get("refresh_token")
        expires_in = token_info.get("expires_in", 3600)

        # Get user profile
        user_profile = await spotify_service.get_current_user(access_token)

        # Save/update user in database
        statement = select(User).where(User.spotify_id == user_profile["id"])
        result = await session.execute(statement)
        db_user = result.scalar_one_or_none()

        if db_user:
            # Update existing user
            db_user.access_token = access_token
            db_user.refresh_token = refresh_token
            db_user.token_expires_at = datetime.utcnow() + timedelta(
                seconds=expires_in
            )
            db_user.last_active_at = datetime.utcnow()
        else:
            # Create new user
            db_user = User(
                spotify_id=user_profile["id"],
                display_name=user_profile.get("display_name", "Unknown"),
                email=user_profile.get("email"),
                country=user_profile.get("country", ""),
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
                last_active_at=datetime.utcnow(),
            )
            session.add(db_user)

        await session.commit()

        # Redirect to dashboard
        return RedirectResponse(url="/dashboard?authenticated=true")

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@router.get("/me")
async def get_current_user(
    session: AsyncSession = Depends(get_async_session),
):
    """Get current user profile"""
    # This would require extracting token from session/header
    # Implementation depends on auth strategy
    pass


@router.post("/logout")
async def logout():
    """Logout user (invalidate session)"""
    # Session-based logout
    pass
