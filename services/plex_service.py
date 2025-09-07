"""Modern Plex service with async support."""

import asyncio
import logging
from datetime import timedelta
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET
import httpx
from fastapi import HTTPException

from config import PlexConfig, settings


logger = logging.getLogger(__name__)


class PlexSession:
    """Represents a Plex user session."""
    
    def __init__(self, session_data: dict):
        self.user = session_data.get("User", {}).get("@title", "")
        self.session_key = session_data.get("@sessionKey", "")
        self.view_offset = int(session_data.get("@viewOffset", 0))
        self.media = session_data.get("Media", {})
        self.metadata = session_data
    
    @property
    def current_time_str(self) -> str:
        """Get current playback time as formatted string."""
        return self._milliseconds_to_time_string(self.view_offset)
    
    @property
    def media_path(self) -> str:
        """Get the file path of the currently playing media."""
        if isinstance(self.media, list) and self.media:
            parts = self.media[0].get("Part", [])
            if isinstance(parts, list) and parts:
                return parts[0].get("@file", "")
        return ""
    
    @property
    def media_fps(self) -> float:
        """Get the frame rate of the currently playing media."""
        if isinstance(self.media, list) and self.media:
            return float(self.media[0].get("@frameRate", 24.0))
        return 24.0
    
    @property
    def media_title(self) -> str:
        """Get the title of the currently playing media."""
        title = self.metadata.get("@title", "")
        if self.metadata.get("@type") == "episode":
            show = self.metadata.get("@grandparentTitle", "")
            return f"{show} - {title}" if show else title
        return title
    
    @property
    def media_type(self) -> str:
        """Get the type of media (movie, episode, etc.)."""
        return self.metadata.get("@type", "unknown")
    
    @staticmethod
    def _milliseconds_to_time_string(milliseconds: int) -> str:
        """Convert milliseconds to HH:MM:SS format."""
        time_str = str(timedelta(milliseconds=milliseconds))
        if len(time_str.split(":")[0]) < 2:
            time_str = f"0{time_str}"
        return time_str.split(".")[0]


class PlexService:
    """Service for interacting with Plex Media Server."""
    
    def __init__(self, config: PlexConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=30.0)
        self._base_params = {"X-Plex-Token": config.token}
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def get_current_sessions(self) -> List[PlexSession]:
        """Get all current Plex sessions."""
        try:
            url = f"{self.config.url}/status/sessions"
            response = await self.client.get(url, params=self._base_params)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            sessions = []
            
            for video_elem in root.findall('.//Video'):
                try:
                    # Convert XML element to dict-like structure for easier handling
                    session_data = self._xml_to_dict(video_elem)
                    sessions.append(PlexSession(session_data))
                except Exception as e:
                    logger.warning(f"Failed to parse session: {e}")
                    continue
                    
            return sessions
            
        except httpx.RequestError as e:
            logger.error(f"Failed to fetch Plex sessions: {e}")
            raise HTTPException(status_code=503, detail="Unable to connect to Plex server")
        except httpx.HTTPStatusError as e:
            logger.error(f"Plex server error: {e}")
            raise HTTPException(status_code=e.response.status_code, detail="Plex server error")
    
    async def get_user_session(self, username: str) -> Optional[PlexSession]:
        """Get the current session for a specific user."""
        sessions = await self.get_current_sessions()
        
        for session in sessions:
            if session.user.lower() == username.lower():
                return session
        
        return None
    
    async def get_media_details(self, media_key: str) -> dict:
        """Get detailed information about a media item."""
        try:
            url = f"{self.config.url}{media_key}"
            response = await self.client.get(url, params=self._base_params)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            return self._xml_to_dict(root)
            
        except httpx.RequestError as e:
            logger.error(f"Failed to fetch media details: {e}")
            raise HTTPException(status_code=503, detail="Unable to connect to Plex server")
    
    def _xml_to_dict(self, element: ET.Element) -> dict:
        """Convert XML element to dictionary."""
        result = {"@tag": element.tag}
        
        # Add attributes with @ prefix
        for key, value in element.attrib.items():
            result[f"@{key}"] = value
        
        # Add child elements
        children = {}
        for child in element:
            child_dict = self._xml_to_dict(child)
            child_tag = child.tag
            
            if child_tag in children:
                if not isinstance(children[child_tag], list):
                    children[child_tag] = [children[child_tag]]
                children[child_tag].append(child_dict)
            else:
                children[child_tag] = child_dict
        
        result.update(children)
        
        # Add text content if present
        if element.text and element.text.strip():
            result["#text"] = element.text.strip()
            
        return result


# Global service instance
async def get_plex_service():
    """Dependency to get Plex service instance."""
    config = PlexConfig.from_settings()
    service = PlexService(config)
    try:
        yield service
    finally:
        await service.client.aclose()