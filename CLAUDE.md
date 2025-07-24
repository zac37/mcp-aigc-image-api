# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a dual-purpose Python project providing a comprehensive Images API service:

1. **Images API Service**: A multi-model image generation service supporting 15+ AI image models
2. **Dual Protocol Support**: Both FastAPI (REST) and MCP (Model Context Protocol) interfaces

## Key Architecture

### Images API Service
- **Dual Service Setup**: Both FastAPI (port 5512) and FastMCP (port 5513) services run independently
- **FastAPI Service**: Main API service with rate limiting, CORS support, and async HTTP client
- **MCP Service**: FastMCP server providing streamable HTTP protocol for image generation tools
- **Core Framework**: FastMCP 2.5.1 with multiple AI image model integrations
- **Transport**: Streamable HTTP using POST requests with Server-Sent Events responses

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

### Service Management
```bash
# Start both services (recommended)
./restart.sh

# Check service status
./status.sh

# Stop services
./stop.sh
```

### Development Setup
```bash
# Create virtual environment (Python 3.11+ required)
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running Services
```bash
# Run MCP server directly (streamable HTTP on port 5513)
python scripts/run_mcp_streamable.py

# Run FastAPI server directly (port 5512)
python main.py

# Both services together
./restart.sh
```

### Testing
```bash
# Test all API endpoints
python scripts/test_api.py

# Health check
curl http://localhost:5512/api/health
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

### MCP Protocol Implementation
- **Transport**: Streamable HTTP (not standard SSE)
- **Request Format**: POST to `/mcp/v1` with JSON payload
- **Response Format**: Server-Sent Events with `mcp-session-id` headers
- **Session Management**: Handled via custom headers for stateful operations

### Configuration Management
- **Centralized Config**: `core/config.py` using Pydantic models
- **Environment Variables**: Loaded via python-dotenv from `.env` files
- **API Keys**: Centralized in configuration (default uses example project's key)
- **Performance Tuning**: Connection pooling, rate limiting, async HTTP client

### Service Architecture
- **Independent Services**: FastAPI and MCP services run as separate processes
- **Rate Limiting**: 1000 requests/minute with burst capacity
- **Async Operations**: aiohttp for API calls, FastAPI async endpoints
- **Error Handling**: Comprehensive error handling with retry logic
- **Logging**: Multi-level logging with colored console output and file rotation

## Important Notes

- **Security**: API key configured in core/config.py (should be changed for production)
- **Protocol**: MCP service uses streamable HTTP protocol (POST requests with SSE responses)
- **Service Management**: Both services run independently and can be managed via shell scripts
- **Dependencies**: Requires Python 3.11+, uses FastMCP 2.5.1 and FastAPI
- **Multi-Model Support**: Unified interface for 15+ different image generation models
- **Logging**: Comprehensive logging system with separate log files for different components

## Development Guidelines

- **Code Style**: Follow existing patterns in example project
- **Configuration**: Use centralized config in core/config.py
- **Logging**: Use appropriate logger for each component
- **Error Handling**: Implement proper error handling with ImagesAPIError
- **Testing**: Add tests to scripts/test_api.py for new endpoints
- **Documentation**: Update README.md and API documentation for new features