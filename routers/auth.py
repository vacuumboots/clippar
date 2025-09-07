"""Authentication endpoints."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import httpx

from config import settings


logger = logging.getLogger(__name__)
router = APIRouter()


class TokenRequest(BaseModel):
    """Request with Plex token."""
    token: str


class AuthResponse(BaseModel):
    """Authentication response."""
    success: bool
    username: str
    user_id: Optional[str] = None
    message: Optional[str] = None


class PlexAuthService:
    """Service for Plex authentication."""
    
    @staticmethod
    async def verify_plex_token(token: str) -> Optional[dict]:
        """Verify Plex token and get user information."""
        try:
            headers = {
                'X-Plex-Token': token,
                'Accept': 'application/json'
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get user information from Plex
                response = await client.get(
                    'https://plex.tv/api/v2/user',
                    headers=headers
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    return {
                        'username': user_data.get('username', user_data.get('title', 'Unknown')),
                        'user_id': str(user_data.get('id', '')),
                        'email': user_data.get('email', ''),
                        'thumb': user_data.get('thumb', '')
                    }
                else:
                    logger.warning(f"Plex auth failed with status {response.status_code}")
                    return None
                    
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to Plex.tv: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during Plex auth: {e}")
            return None


@router.post("/verify", response_model=AuthResponse)
async def verify_token(request: TokenRequest):
    """Verify Plex authentication token."""
    auth_service = PlexAuthService()
    user_info = await auth_service.verify_plex_token(request.token)
    
    if user_info:
        return AuthResponse(
            success=True,
            username=user_info['username'],
            user_id=user_info.get('user_id'),
            message="Authentication successful"
        )
    else:
        raise HTTPException(
            status_code=401,
            detail="Invalid Plex token or unable to verify with Plex.tv"
        )


@router.get("/status")
async def auth_status():
    """Get authentication status and configuration."""
    return {
        "auth_required": True,
        "auth_method": "plex_token",
        "server_configured": bool(settings.plex_url and settings.plex_token)
    }