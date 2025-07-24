# Technology Stack

## Core Technologies

### Meta Marketing API Service
- **Python 3.11+** - Primary runtime environment
- **FastAPI 0.115.12** - Web framework for HTTP APIs
- **FastMCP 2.5.1** - MCP protocol framework
- **Uvicorn** - ASGI server for FastAPI
- **Pydantic 2.0+** - Data validation and serialization
- **httpx/aiohttp** - Async HTTP clients for external API calls
- **Meta Graph API v22.0** - Facebook/Meta advertising API

### API Documentation Scraper
- **Python 3** - Runtime environment
- **aiohttp 3.8+** - Async HTTP client for web scraping
- **BeautifulSoup4** - HTML parsing and extraction
- **lxml** - XML/HTML parser backend
- **aiofiles** - Async file operations

## Development Tools
- **Docker & Docker Compose** - Containerization and orchestration
- **Virtual environments** - Python dependency isolation (.venv_py311)
- **Environment variables** - Configuration management via .env files

## Common Commands

### Service Management
```bash
# Start/restart services (recommended)
./restart.sh

# Check service status
./status.sh

# Stop services
./stop.sh

# Deploy to production
./deploy-prod.sh
```

### Development Setup
```bash
# Create virtual environment
python3.11 -m venv .venv_py311
source .venv_py311/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI service
python main.py

# Run MCP service independently
python scripts/run_mcp_streamable.py
```

### Docker Operations
```bash
# Build and run with Docker Compose
docker-compose up -d

# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f
```

### Testing
```bash
# Test MCP protocol
python scripts/test_correct_protocol.py

# Run API documentation scraper
cd crawl && python scrape_chatfire_simple.py
```

## Architecture Patterns
- **Layered Architecture**: Routers → Services → Clients
- **Async/Await**: Non-blocking I/O operations
- **Dependency Injection**: FastAPI's dependency system
- **Configuration Management**: Centralized via Pydantic models
- **Rate Limiting**: Sliding window algorithm for API protection