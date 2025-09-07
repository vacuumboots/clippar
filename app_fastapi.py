"""FastAPI application for Clipplex."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from config import settings


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Clipplex application")
    
    # Create required directories
    media_dirs = [
        Path(settings.media_static_path) / "videos",
        Path(settings.media_static_path) / "images"
    ]
    
    for directory in media_dirs:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Clipplex application")


# Create FastAPI app
app = FastAPI(
    title="Clipplex",
    description="Extract video clips from Plex media streams",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path(settings.media_static_path).parent
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Import and include routers
from routers import plex, clips, auth

app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(plex.router, prefix="/api/plex", tags=["plex"])  
app.include_router(clips.router, prefix="/api/clips", tags=["clips"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Clipplex API v2.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app_fastapi:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )