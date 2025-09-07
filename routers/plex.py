"""Plex API endpoints."""

from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.plex_service import PlexService, get_plex_service


router = APIRouter()


class StreamInfo(BaseModel):
    """Current stream information."""
    username: str
    media_title: str
    current_time: str
    file_path: str
    media_type: str


class SessionsResponse(BaseModel):
    """Response for active sessions."""
    sessions: List[Dict]
    count: int


@router.get("/sessions", response_model=SessionsResponse)
async def get_sessions(plex_service: PlexService = Depends(get_plex_service)):
    """Get all active Plex sessions."""
    sessions = await plex_service.get_current_sessions()
    
    session_data = []
    for session in sessions:
        session_data.append({
            "username": session.user,
            "media_title": session.media_title,
            "current_time": session.current_time_str,
            "media_type": session.media_type,
            "session_key": session.session_key
        })
    
    return SessionsResponse(sessions=session_data, count=len(session_data))


@router.get("/stream/{username}", response_model=StreamInfo)
async def get_current_stream(
    username: str, 
    plex_service: PlexService = Depends(get_plex_service)
):
    """Get current stream information for a specific user."""
    session = await plex_service.get_user_session(username)
    
    if not session:
        raise HTTPException(
            status_code=404, 
            detail=f"No active stream found for user {username}"
        )
    
    return StreamInfo(
        username=session.user,
        media_title=session.media_title,
        current_time=session.current_time_str,
        file_path=session.media_path,
        media_type=session.media_type
    )