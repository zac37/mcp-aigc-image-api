# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive AI-powered image and video generation service with dual protocol support:

1. **Multi-Model AI Service**: Supporting 15+ image generation models and video generation (Veo3)
2. **Dual Protocol Support**: Both FastAPI (REST) and MCP (Model Context Protocol) interfaces
3. **Async Task Processing**: Celery-based background task processing with Redis backend
4. **File Storage**: MinIO integration for generated content storage with metadata management
5. **Production Ready**: Full Docker deployment with monitoring and health checks

## Core Architecture

### Service Architecture
- **FastAPI Service** (port 5512): Main REST API with async operations
- **MCP Service** (port 5513): FastMCP server using streamable-HTTP transport  
- **Celery Worker**: Background task processing for video generation monitoring
- **Celery Beat**: Scheduled task dispatcher for periodic operations
- **Redis**: Message broker for Celery and task queue management
- **MinIO**: Object storage for generated images/videos with metadata

### Key Design Patterns
- **Unified Client Pattern**: Single `ImagesAPIClient` handles all model integrations
- **Async Task Queue**: Custom `SimpleTaskQueue` for video task management
- **Configuration Management**: Centralized Pydantic-based config with environment override
- **Comprehensive Logging**: Multi-level logging with file rotation and colored output

### Supported Models

1. **GPT (DALL-E)**: OpenAI's DALL-E 2 and DALL-E 3 models
2. **Recraft**: Professional image creation tool
3. **即梦3.0 (Seedream)**: Advanced image generation technology
4. **即梦垫图 (SeedEdit)**: Intelligent editing based on existing images
5. **FLUX**: High-quality open-source image generation model
6. **Recraftv3**: Latest version of Recraft image generation
7. **Cogview**: Tsinghua University's image generation model
8. **混元 (Hunyuan)**: Tencent's image generation technology
9. **Kling**: Kuaishou's image generation service
10. **Stable Diffusion**: Classic open-source image generation model
11. **Kolors**: Colorful image generation technology
12. **虚拟换衣 (Virtual Try-on)**: AI-driven virtual clothing try-on
13. **flux-kontext**: Context-aware image generation
14. **海螺图片 (Hailuo)**: Hailuo AI's image generation
15. **Doubao**: ByteDance's image generation

### Directory Structure

```
mcp_aigc_image_api/
├── core/                     # Configuration, logging, and API client
│   ├── config.py            # Centralized configuration management
│   ├── logger.py            # Logging system with colored output
│   └── images_client.py     # Unified API client for all image models
├── routers/                 # FastAPI routes and MCP tool definitions
│   ├── api.py              # FastAPI endpoints for all models
│   └── mcp/                # MCP tool functions and service
│       ├── main.py         # MCP service main program
│       └── images_tools.py # MCP tool function implementations
├── services/               # Business logic layer
│   └── images_service.py   # Image generation service logic
├── scripts/                # Service management and test scripts
│   ├── run_mcp_streamable.py # MCP service startup script
│   └── test_api.py         # API testing script
├── main.py                 # FastAPI main application
├── requirements.txt        # Python dependencies
├── restart.sh             # Service restart script
├── stop.sh               # Service stop script
└── status.sh             # Service status check script
```

## Essential Commands

### Development Setup
```bash
# Python 3.11+ is required
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Local Development
```bash
# Start both services (recommended for development)
./restart.sh

# Start services individually
python main.py                          # FastAPI service (port 5512)
python scripts/run_mcp_streamable.py    # MCP service (port 5513)

# Start Celery worker for background tasks  
celery -A celery_config worker --loglevel=info --pool=threads --concurrency=4

# Start Celery beat for scheduled tasks
celery -A celery_config beat --loglevel=info

# Check service status
./status.sh

# Stop all services
./stop.sh
```

### Testing and Verification
```bash
# Test all API endpoints
python scripts/test_api.py

# Health check endpoints
curl http://localhost:5512/api/health      # FastAPI health
curl http://localhost:5513/mcp/v1         # MCP service (returns error without proper headers)

# Check Celery worker status
celery -A celery_config inspect active
celery -A celery_config inspect stats
```

### Docker Deployment
```bash
# Production deployment to remote server
./deploy-remote-production.sh

# Local Docker build and test
docker-compose -f docker-compose.production.yml up --build

# Check Docker compatibility before deployment
./check_docker_compatibility.sh
```

## Service Configuration

### Images API Service
- **FastAPI Service**: http://localhost:5512 (API docs at /docs)
- **MCP Service**: http://localhost:5513 (MCP endpoint at /mcp/v1)
- **API Key**: Configured in core/config.py (uses example project's key)
- **Logs**: `fastapi_service.log`, `mcp_service.log`, detailed logs in `logs/` directory

### Supported Endpoints

#### FastAPI Endpoints
- `/api/gpt/generations` - GPT/DALL-E image generation
- `/api/recraft/generate` - Recraft image generation
- `/api/seedream/generate` - 即梦3.0 image generation
- `/api/seededit/generate` - 即梦垫图 image editing
- `/api/flux/create` - FLUX image creation
- `/api/health` - Service health check

#### MCP Tools
- `create_gpt_image` - GPT image generation tool
- `create_recraft_image` - Recraft image generation tool
- `create_seedream_image` - Seedream image generation tool
- `create_seededit_image` - SeedEdit image editing tool
- `create_flux_image` - FLUX image creation tool

## Architecture Details

### Task Processing System
- **Simple Task Queue**: Custom queue implementation in `core/simple_task_queue.py` for video generation
- **Celery Integration**: Background processing with Redis broker for complex workflows
- **Beat Scheduler**: Periodic tasks configured in `celery_config.py` (monitor-video-tasks every 60s)
- **Task Types**: `VideoTask` for Veo3 generation, `ImageTask` for synchronous operations

### MCP Protocol Implementation
- **Transport**: Streamable HTTP with custom headers (not standard Server-Sent Events)
- **Tools Available**: `create_gpt_image`, `create_recraft_image`, `create_seedream_image`, etc.
- **Session Management**: Stateless operations with request-scoped context
- **FastMCP Framework**: Version 2.5.1 with streamable HTTP transport

### Storage and Persistence
- **MinIO Integration**: Object storage with automatic metadata collection
- **Redis Backend**: Task queues, results storage, and metadata caching
- **File Organization**: Structured paths by date/model: `ai_generated/videos/2025/08/01/`
- **Metadata Management**: Comprehensive tracking of generation parameters and results

### Configuration Architecture
- **Pydantic Models**: Type-safe configuration with validation in `core/config.py`
- **Environment Override**: `.env` file support with sensible defaults
- **Multi-Service Config**: Separate sections for FastAPI, MCP, Celery, Redis, MinIO
- **External Service Integration**: Google Vertex AI, JARVIS callback endpoints

## Development Guidelines

### Code Organization
- **Configuration**: All config in `core/config.py` using Pydantic models with environment overrides
- **Logging**: Use component-specific loggers via `core.logger.get_logger(__name__)`
- **Error Handling**: Custom `ImagesAPIError` for API-specific exceptions
- **Async Patterns**: Use `aiohttp` for external API calls, `asyncio` for concurrent operations

### Key Integration Points
- **Adding New Models**: Extend `ImagesAPIClient` in `core/images_client.py` and add routes in `routers/api.py`
- **MCP Tools**: Define in `routers/mcp/images_tools.py` following existing patterns
- **Background Tasks**: Add to `celery_tasks.py` and register in `celery_config.py`
- **Storage Operations**: Use `MinIOClient` from `core/minio_client.py` with metadata tracking

### Docker and Deployment
- **Multi-Service Container**: Single container runs FastAPI, MCP, Celery Worker, and Celery Beat
- **External Dependencies**: Requires Redis (jarvis_redis) and MinIO (jarvis_minio) services
- **Health Checks**: FastAPI has `/api/health`, Docker health check configured
- **Entrypoint Management**: `docker-entrypoint.sh` handles service orchestration and monitoring

### Critical Implementation Details
- **Global Variable Management**: Client instances stored as module-level globals with proper cleanup
- **PID Management**: Docker entrypoint writes PIDs to temp files for monitoring
- **Permission Handling**: Log directory requires 777 permissions in Docker
- **Network Dependencies**: Uses `jarvis-v2_default` Docker network for external service access

### Testing Strategy
- **API Testing**: `scripts/test_api.py` for endpoint validation
- **Health Checks**: Multiple endpoints for service verification
- **Celery Monitoring**: Built-in inspect commands for task queue status
- **Docker Validation**: `check_docker_compatibility.sh` for deployment readiness