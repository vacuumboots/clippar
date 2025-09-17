# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Application Overview

Clippar is a Flask-based web application that extracts video clips from media files being streamed through Plex. It allows users to create short video clips and snapshots from currently playing content.

## Architecture

### Core Components

- **Main Entry Point**: `main.py` - Simple Flask app launcher
- **API Layer**: `clipparAPI.py` - Core business logic with four main classes:
  - `PlexInfo`: Handles Plex server communication and session management
  - `Snapshot`: Extracts frame snapshots using FFmpeg
  - `Video`: Creates video clips with metadata preservation
  - `Utils`: Utility functions for time conversion, file management, and Streamable uploads
- **Web Layer**: `app/` directory containing Flask application:
  - `__init__.py`: Flask app initialization and directory setup
  - `routes.py`: HTTP endpoints and request handling
  - `forms.py`: WTForms definitions for user input validation
  - `templates/`: HTML templates (base.html, instant_video.html, instant_snapshot.html, login.html)
  - `static/`: CSS, JavaScript, and generated media files

### Key Features

- Real-time Plex session monitoring via XML API
- FFmpeg-based video extraction with metadata preservation
- Frame-by-frame snapshot generation
- Streamable.com integration for clip sharing
- Web UI for clip creation and management

## Development Commands

### Running the Application

```bash
# Local development
flask run --host 0.0.0.0

# Docker build
docker build -t clippar .

# Docker run with environment variables
docker run -d --name clippar -p 9945:5000 \
  -v /media:/media \
  -v /volumes/clippar:/app/app/static/media \
  -e PLEX_URL=http://plex:32400 \
  -e PLEX_TOKEN=your_token \
  clippar:latest
```

### Dependencies

Install Python dependencies:
```bash
pip install -r requirements.txt
```

Required external dependency: FFmpeg (handled in Docker container)

## Environment Variables

Required for operation:
- `PLEX_URL`: Plex server URL (e.g., http://plex:32400)
- `PLEX_TOKEN`: Plex authentication token

Optional:
- `STREAMABLE_LOGIN`: Streamable.com username for uploads
- `STREAMABLE_PASSWORD`: Streamable.com password for uploads
- `PUID`/`PGID`: User/group IDs for Docker
- `TZ`: Timezone setting

## File Structure Notes

- Media files are accessed via absolute paths that must match Plex's media library paths
- Generated clips stored in `/app/app/static/media/videos/`
- Generated snapshots stored in `/app/app/static/media/images/`
- Static files served from `/app/app/static/`

## API Endpoints

Key routes in `app/routes.py`:
- `/get_current_stream` - Get active Plex session info
- `/create_video` - Generate video clip from time range
- `/get_instant_snapshot` - Extract frames at current playback time
- `/streamable_upload` - Upload clips to Streamable.com

## Known Technical Debt

- Hardcoded username "jonike" in snapshot route (`routes.py:17`)
- Static secret key in Flask config (`app/__init__.py:10`)
- Incomplete authentication system (`routes.py:87-93`)
- Direct subprocess calls for FFmpeg in Snapshot class