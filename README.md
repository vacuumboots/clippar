# Clippar

## forked from [jo-nike/clipplex](https://github.com/jo-nike/clipplex)


Have you ever, while watching something on your Plex server, wanted to easily extract a clip out of a good movie or TV show you're watching to share it with your friends or family? While this was always possible, the process can be complex for something "so simple".

![](https://github.com/vacuumboots/clippar/blob/master/example.gif)

## Description

Clippar is a modern web application that extracts video clips and snapshots from media files being streamed through Plex. It allows users to create short video clips with preserved metadata from currently playing content, making it easy to share memorable moments from your media library.

**Key Features:**
- **Real-time Plex Integration**: Monitor active Plex sessions and extract clips from currently playing media
- **Video Clip Creation**: Generate MP4 clips with custom start/end times and preserved metadata
- **Snapshot Extraction**: Capture frame-perfect screenshots from any point in playback
- **Modern Architecture**: Built with FastAPI for performance and reliability
- **Secure Authentication**: Plex token-based authentication system
- **Docker Ready**: Fully containerized for easy deployment

## Architecture

The application has been modernized with a dual-architecture approach:

- **FastAPI Application** (`app_fastapi.py`): Modern, async API server (recommended)
- **Legacy Flask Application** (`main.py`): Deprecated, maintained for compatibility

### Core Components

- **Services Layer**: Modular business logic with `PlexService` and `ClipService`
- **API Routers**: RESTful endpoints for authentication, clip management, and Plex integration
- **Security**: Path traversal protection, authentication middleware, and secure session management

## Environment Variables

### Required Configuration

| Variable    | Description                              | Example                    |
|-------------|------------------------------------------|----------------------------|
| PLEX_URL    | URL to your Plex server                  | `http://plex:32400`        |
| PLEX_TOKEN  | Plex authentication token                | `your_plex_token_here`     |

### Optional Configuration

| Variable           | Description                           | Default                    |
|--------------------|---------------------------------------|----------------------------|
| SECRET_KEY         | FastAPI secret key                    | Auto-generated             |
| FLASK_SECRET_KEY   | Flask secret key (legacy)             | Auto-generated             |
| DEBUG              | Enable debug mode                     | `false`                    |
| HOST               | Server host                           | `0.0.0.0`                  |
| PORT               | Server port                           | `5000`                     |
| PUID               | User ID for Docker                    | `1000`                     |
| PGID               | Group ID for Docker                   | `1000`                     |
| TZ                 | Timezone                              | `America/New_York`         |

**Finding your Plex token**: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

## Docker Deployment

### Volume Requirements

You need to mount two locations:

1. **Media Directory**: Mount your media files to `/media` (must match Plex's media paths exactly, as paths are absolute)
2. **Output Directory**: Mount the clip/snapshot output location to `/app/app/static/media`

### Network Requirements

- Must be on the same Docker network as your Plex instance
- Port 5000 is used for the web interface
- Typically exposed on host port 9945

### Quick Start

```bash
docker run -d \
  --name clippar \
  --network your_plex_network \
  -p 9945:5000 \
  -v /path/to/your/media:/media:ro \
  -v /path/to/clippar/output:/app/app/static/media \
  -e PLEX_URL=http://plex:32400 \
  -e PLEX_TOKEN=your_plex_token \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=America/New_York \
  --restart unless-stopped \
  vacuumboots/clippar:latest
```

### Docker Compose Example

```yaml
version: "3.8"

services:
  clippar:
    image: vacuumboots/clippar:latest
    container_name: clippar
    environment:
      - PLEX_URL=http://plex:32400
      - PLEX_TOKEN=your_plex_token
      - SECRET_KEY=change-this-in-production
      - FLASK_SECRET_KEY=change-this-in-production
      - DEBUG=false
      - PUID=1000
      - PGID=1000
      - TZ=America/New_York
    volumes:
      # Media directories (must match Plex paths)
      - /path/to/your/tv:/tv:ro
      - /path/to/your/movies:/movies:ro
      - /path/to/your/media:/media:ro
      # Output directory for generated clips
      - ./clippar-data:/app/app/static/media
    ports:
      - "9945:5000"
    networks:
      - plex-network
    restart: unless-stopped
    depends_on:
      - plex

networks:
  plex-network:
    external: true
```

## API Endpoints

The FastAPI application provides a modern REST API:

### Authentication
- `POST /auth/verify` - Verify Plex token
- `GET /auth/status` - Get authentication status

### Clip Management
- `POST /clips/create` - Create video clip
- `GET /clips/videos` - List created videos
- `GET /clips/images` - List snapshots
- `DELETE /clips/file` - Delete media file (authenticated)

### Plex Integration
- `GET /plex/sessions` - Get active Plex sessions
- `POST /plex/snapshot` - Create snapshot from current playback

## Security Features

- **Authentication Required**: All destructive operations require valid Plex token
- **Path Traversal Protection**: File operations are restricted to media directories
- **Input Validation**: Strict validation on all user inputs
- **Secure Secrets**: Environment-based secret key management
- **CORS Protection**: Configurable cross-origin policies

## Development

### Running Locally

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables in `.env` file
4. Run FastAPI app: `python app_fastapi.py`
5. Access at `http://localhost:5000`

### Legacy Flask Support

The original Flask application is still available but deprecated:

```bash
python main.py  # Will show deprecation warning
```

## Migration Notes

**From v0.0.3 to Current:**
- Streamable integration has been removed
- Flask app is deprecated in favor of FastAPI
- Enhanced security with authentication requirements
- Improved error handling and logging
- Modern async architecture

## Version History

* **Current**
    - Modernized to FastAPI architecture
    - Removed Streamable integration
    - Added authentication and security improvements
    - Enhanced path traversal protection
    - Improved Docker configuration

* **0.0.3**
    - Initial Flask-based release
    - Basic clip extraction functionality
    - Streamable upload support

## Authors

- **Jo Nike** - Original creator
- **vacuumboots** - Author of the fork

## License

Distributed under the MIT License. See the LICENSE file for more information.




