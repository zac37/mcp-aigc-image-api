# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a dual-purpose Python project containing:

1. **Meta Marketing API MCP Service** (`meta-curl-api/`): A comprehensive MCP service providing 42 Meta advertising API tool functions using FastMCP framework with streamable HTTP protocol support
2. **Web Scraping Tools** (`crawl/`): Automated web scraping utilities for analyzing and extracting API documentation

## Key Architecture

### Meta Marketing API Service (`meta-curl-api/`)
- **Dual Service Setup**: Both FastAPI (port 5501) and FastMCP (port 5500) services run independently
- **FastAPI Service**: Main API service with rate limiting, CORS support, and async HTTP client
- **MCP Service**: FastMCP server providing streamable HTTP protocol (POST + SSE) for Meta Marketing API tools
- **Core Framework**: FastMCP 2.5.1 with Meta Graph API v22.0
- **Transport**: Streamable HTTP using POST requests with Server-Sent Events responses

### Directory Structure

```
mcp_aigc_api/
├── meta-curl-api/              # Main Meta Marketing API MCP service
│   ├── core/                   # Configuration, logging, and Facebook API client
│   ├── routers/               # FastAPI routes and MCP tool definitions
│   │   ├── api.py            # FastAPI endpoints
│   │   └── mcp/              # MCP tool functions (accounts, campaigns, ads, etc.)
│   ├── services/             # Business logic layer for Meta API interactions  
│   ├── scripts/              # Service management and test scripts
│   ├── middleware/           # Rate limiting middleware
│   └── docs/                 # Technical documentation
└── crawl/                     # Web scraping and analysis tools
    ├── scraper_selenium.py    # Selenium-based web scraper
    ├── analyze_apifox.py      # API documentation analyzer
    └── models.py              # Data models for scraped content
```

## Essential Commands

### Service Management (meta-curl-api/)
```bash
cd meta-curl-api

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
python3.11 -m venv .venv_py311
source .venv_py311/bin/activate

# Install dependencies for Meta API service
cd meta-curl-api && pip install -r requirements.txt

# Install dependencies for crawl tools (separate requirements)
cd crawl && pip install -r requirements.txt
```

### Running Services
```bash
cd meta-curl-api

# Run MCP server directly (streamable HTTP on port 5500)
python scripts/run_mcp_streamable.py

# Run FastAPI server directly (port 5501)
python main.py

# Docker deployment (production)
docker-compose up -d
```

### Testing and Development
```bash
cd meta-curl-api

# Test MCP protocol connectivity
python scripts/test_correct_protocol.py

# Update access token
python scripts/update_access_token.py

# Web scraping tools
cd ../crawl
python scrape_chatfire_docs.py
python analyze_apifox.py
```

## Service Configuration

### Meta Marketing API Service
- **FastAPI Service**: http://localhost:5501 (API docs at /docs)
- **MCP Service**: http://localhost:5500 (MCP endpoint at /mcp/v1)
- **Virtual Environment**: .venv_py311 (Python 3.11+)
- **Logs**: `meta-curl-api/mcp_service.log`, `fastapi_service.log`, `restart.log`

### Web Scraping Tools
- **Configuration**: `crawl/config.py`
- **Models**: Pydantic models in `crawl/models.py`
- **Analysis Results**: JSON files in `crawl/` directory

## Architecture Details

### MCP Protocol Implementation
- **Transport**: Streamable HTTP (not standard SSE)
- **Request Format**: POST to `/mcp/v1` with JSON payload
- **Response Format**: Server-Sent Events with `mcp-session-id` headers
- **Session Management**: Handled via custom headers for stateful operations

### Configuration Management
- **Centralized Config**: `meta-curl-api/core/config.py` using Pydantic models
- **Environment Variables**: Loaded via python-dotenv from `.env` files
- **Facebook API**: Dynamic token handling (no environment variable storage)
- **Performance Tuning**: Connection pooling, rate limiting, async HTTP client

### Service Architecture
- **Independent Services**: FastAPI and MCP services run as separate processes
- **Rate Limiting**: 1000 requests/minute with burst capacity via custom middleware
- **Async Operations**: aiohttp for Facebook API calls, FastAPI async endpoints
- **Error Handling**: Custom Facebook API error handling with retry logic

## Important Notes

- **Security**: Access tokens must be provided explicitly in each API request (not via environment variables)
- **Protocol**: MCP service uses streamable HTTP protocol (POST requests with SSE responses), not standard HTTP streaming
- **Service Management**: Both services run independently and can be managed via the provided shell scripts
- **Dependencies**: Main service requires Python 3.11+, crawl tools may have different requirements
- **Docker Support**: Production deployment configured with docker-compose for containerized environments
- **Logging**: Comprehensive logging system with separate log files for different components