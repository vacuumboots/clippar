"""Modern clip creation service."""

import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import ffmpeg

from config import settings, StreamableConfig
from services.plex_service import PlexService, PlexSession


logger = logging.getLogger(__name__)


class ClipRequest:
    """Represents a clip creation request."""
    
    def __init__(self, username: str, start_time: str, end_time: str):
        self.username = username
        self.start_time = start_time
        self.end_time = end_time
        self.duration = self._calculate_duration(start_time, end_time)
        self.timestamp = int(time.time())
    
    def _calculate_duration(self, start: str, end: str) -> int:
        """Calculate clip duration in seconds."""
        start_parts = start.split(":")
        start_seconds = int(start_parts[0]) * 3600 + int(start_parts[1]) * 60 + int(start_parts[2])
        
        end_parts = end.split(":")
        end_seconds = int(end_parts[0]) * 3600 + int(end_parts[1]) * 60 + int(end_parts[2])
        
        return end_seconds - start_seconds


class ClipService:
    """Service for creating video clips."""
    
    def __init__(self):
        self.media_path = Path(settings.media_static_path)
        self.videos_path = self.media_path / "videos"
        self.images_path = self.media_path / "images"
        
        # Ensure directories exist
        self.videos_path.mkdir(parents=True, exist_ok=True)
        self.images_path.mkdir(parents=True, exist_ok=True)
    
    async def create_clip(
        self, 
        session: PlexSession, 
        clip_request: ClipRequest
    ) -> Dict[str, str]:
        """Create a video clip from Plex session."""
        try:
            # Generate filename
            clean_title = self._sanitize_filename(session.media_title)
            filename = f"{clip_request.username}_{clean_title}_{clip_request.timestamp}"
            output_path = self.videos_path / f"{filename}.mp4"
            
            # Create clip using ffmpeg-python
            await self._extract_video_clip(
                session.media_path,
                clip_request.start_time,
                clip_request.duration,
                output_path,
                session
            )
            
            logger.info(f"Created clip: {output_path}")
            
            return {
                "status": "success",
                "filename": f"{filename}.mp4",
                "path": f"static/media/videos/{filename}.mp4"
            }
            
        except Exception as e:
            logger.error(f"Failed to create clip: {e}")
            raise Exception(f"Clip creation failed: {str(e)}")
    
    async def _extract_video_clip(
        self,
        input_path: str,
        start_time: str,
        duration: int,
        output_path: Path,
        session: PlexSession
    ):
        """Extract video clip using ffmpeg."""
        try:
            # Build metadata
            metadata = {
                "title": session.media_title,
                "comment": session.current_time_str,
                "artist": session.user
            }
            
            # Add show-specific metadata if it's a TV episode
            if session.media_type == "episode":
                show_info = session.metadata
                metadata.update({
                    "show": show_info.get("@grandparentTitle", ""),
                    "season_number": show_info.get("@parentIndex", ""),
                    "episode_id": show_info.get("@index", "")
                })
            
            # Create ffmpeg stream
            stream = ffmpeg.input(input_path, ss=start_time, t=duration)
            
            # Configure output with metadata
            output_kwargs = {
                "vcodec": "libx264",
                "acodec": "aac", 
                "pix_fmt": "yuv420p",
                "crf": 18,
                "map_metadata": -1
            }
            
            # Add metadata to output
            for key, value in metadata.items():
                if value:  # Only add non-empty values
                    output_kwargs[f"metadata:g:{key}"] = str(value)
            
            output = ffmpeg.output(stream, str(output_path), **output_kwargs)
            
            # Run ffmpeg in a thread to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: ffmpeg.run(output, capture_stdout=True, check=True)
            )
            
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else "Unknown ffmpeg error"
            logger.error(f"FFmpeg error: {error_msg}")
            raise Exception(f"Video processing failed: {error_msg}")
    
    async def create_snapshot(
        self, 
        session: PlexSession, 
        num_frames: int = 1
    ) -> Dict[str, str]:
        """Create snapshot frames from current playback position."""
        try:
            timestamp = session.current_time_str.replace(":", "_")
            output_pattern = self.images_path / f"{timestamp}_%03d.jpg"
            
            # Extract frames using ffmpeg
            stream = ffmpeg.input(session.media_path, ss=session.current_time_str)
            output = ffmpeg.output(
                stream, 
                str(output_pattern),
                vframes=num_frames,
                **{"qscale:v": 2}
            )
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: ffmpeg.run(output, capture_stdout=True, check=True)
            )
            
            return {
                "status": "success",
                "timestamp": timestamp,
                "frames": num_frames
            }
            
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else "Unknown ffmpeg error"
            logger.error(f"Snapshot creation failed: {error_msg}")
            raise Exception(f"Snapshot creation failed: {error_msg}")
    
    def get_video_list(self) -> List[Dict]:
        """Get list of created video clips with metadata."""
        videos = []
        
        for video_file in self.videos_path.glob("*.mp4"):
            try:
                # Get metadata using ffprobe
                probe = ffmpeg.probe(str(video_file))
                metadata = probe.get("format", {}).get("tags", {})
                
                videos.append({
                    "file_path": f"static/media/videos/{video_file.name}",
                    "title": metadata.get("title", ""),
                    "original_start_time": metadata.get("comment", ""),
                    "username": metadata.get("artist", ""),
                    "show": metadata.get("show", ""),
                    "episode_number": metadata.get("episode_id", ""),
                    "season_number": metadata.get("season_number", "")
                })
                
            except Exception as e:
                logger.warning(f"Failed to read metadata for {video_file}: {e}")
                continue
        
        return videos
    
    def get_image_list(self) -> List[str]:
        """Get list of created snapshot images."""
        images = []
        for image_file in self.images_path.glob("*.jpg"):
            relative_path = f"static/media/images/{image_file.name}"
            images.append(relative_path)
        return sorted(images)
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a media file."""
        try:
            # Remove 'static/' prefix if present
            if file_path.startswith("static/"):
                file_path = file_path[7:]  # Remove 'static/'
            
            full_path = Path(settings.media_static_path).parent / file_path
            
            if full_path.exists() and full_path.is_file():
                full_path.unlink()
                logger.info(f"Deleted file: {full_path}")
                return True
            else:
                logger.warning(f"File not found: {full_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility."""
        # Remove or replace problematic characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")
        
        # Replace spaces and limit length
        filename = filename.replace(" ", "_")[:50]
        
        return filename
    
    @staticmethod
    def add_time_to_timestamp(current_time: str, seconds_to_add: int) -> str:
        """Add seconds to a time string."""
        time_obj = datetime.strptime(current_time, "%H:%M:%S")
        new_time = time_obj + timedelta(seconds=seconds_to_add)
        return new_time.strftime("%H:%M:%S")