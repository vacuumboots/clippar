"""Clip creation and management endpoints."""

from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from services.clip_service import ClipService, ClipRequest
from services.plex_service import PlexService, get_plex_service
from routers.auth import get_current_user


router = APIRouter()


class CreateClipRequest(BaseModel):
    """Request to create a video clip."""
    username: str
    start_time: str  # HH:MM:SS format
    end_time: str    # HH:MM:SS format


class CreateSnapshotRequest(BaseModel):
    """Request to create a snapshot."""
    username: str
    num_frames: int = 1


class ClipResponse(BaseModel):
    """Response for clip creation."""
    status: str
    filename: str
    path: str


class SnapshotResponse(BaseModel):
    """Response for snapshot creation."""
    status: str
    timestamp: str
    frames: int


class VideoListResponse(BaseModel):
    """Response for video list."""
    videos: List[Dict]


class ImageListResponse(BaseModel):
    """Response for image list."""
    images: List[str]


@router.post("/create", response_model=ClipResponse)
async def create_clip(
    request: CreateClipRequest,
    plex_service: PlexService = Depends(get_plex_service)
):
    """Create a video clip from current Plex stream."""
    # Get user's current session
    session = await plex_service.get_user_session(request.username)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"No active stream found for user {request.username}"
        )
    
    # Create clip request
    clip_request = ClipRequest(
        username=request.username,
        start_time=request.start_time,
        end_time=request.end_time
    )
    
    # Create the clip
    clip_service = ClipService()
    try:
        result = await clip_service.create_clip(session, clip_request)
        return ClipResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/snapshot", response_model=SnapshotResponse)
async def create_snapshot(
    request: CreateSnapshotRequest,
    plex_service: PlexService = Depends(get_plex_service)
):
    """Create snapshot frames from current playback position."""
    # Get user's current session
    session = await plex_service.get_user_session(request.username)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"No active stream found for user {request.username}"
        )
    
    # Create the snapshot
    clip_service = ClipService()
    try:
        result = await clip_service.create_snapshot(session, request.num_frames)
        return SnapshotResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/videos", response_model=VideoListResponse)
async def get_video_list():
    """Get list of created video clips."""
    clip_service = ClipService()
    videos = clip_service.get_video_list()
    return VideoListResponse(videos=videos)


@router.get("/images", response_model=ImageListResponse) 
async def get_image_list():
    """Get list of created snapshot images."""
    clip_service = ClipService()
    images = clip_service.get_image_list()
    return ImageListResponse(images=images)


@router.delete("/file")
async def delete_file(
    file_path: str = Query(..., description="Path to file to delete"),
    current_user: dict = Depends(get_current_user)
):
    """Delete a media file (requires authentication)."""
    clip_service = ClipService()
    success = clip_service.delete_file(file_path)

    if not success:
        raise HTTPException(status_code=404, detail="File not found or could not be deleted")

    return {"status": "success", "message": "File deleted"}


@router.post("/time/add")
async def add_time_to_timestamp(
    current_time: str = Query(..., description="Current time in HH:MM:SS format"),
    seconds_to_add: int = Query(..., description="Seconds to add")
):
    """Add seconds to a timestamp."""
    try:
        new_time = ClipService.add_time_to_timestamp(current_time, seconds_to_add)
        return {"original_time": current_time, "new_time": new_time}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid time format: {str(e)}")