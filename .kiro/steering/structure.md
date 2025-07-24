# Project Structure

## Root Directory Organization

```
mcp_aigc_api/
├── .kiro/                    # Kiro IDE configuration and specs
├── api_docs/                 # Generated API documentation (markdown)
├── crawl/                    # Web scraping tools for API docs
├── meta-curl-api/           # Main Meta Marketing API MCP service
└── documentation files      # Project guides and summaries
```

## Meta Marketing API Service Structure

```
meta-curl-api/
├── core/                    # Core configuration and clients
│   ├── config.py           # Centralized configuration management
│   ├── fb_client.py        # Facebook API HTTP client
│   └── logger.py           # Logging configuration
├── routers/                # API route handlers
│   ├── api.py             # Native Facebook API compatible routes
│   └── mcp/               # MCP protocol tool functions
├── services/               # Business logic layer
│   ├── account.py         # Account management
│   ├── campaign.py        # Campaign operations
│   ├── adset.py          # Ad set management
│   ├── ad.py             # Ad operations
│   ├── creative.py       # Creative management
│   ├── audience.py       # Audience management
│   ├── insights.py       # Analytics and reporting
│   └── page.py           # Facebook page management
├── middleware/             # Custom middleware
│   └── rate_limiter.py    # Request rate limiting
├── scripts/               # Utility and management scripts
│   ├── run_mcp_streamable.py    # MCP server launcher
│   ├── test_correct_protocol.py # Protocol testing
│   └── update_access_token.py   # Token management
├── docs/                  # Technical documentation
├── logs/                  # Application logs
├── main.py               # FastAPI application entry point
├── requirements.txt      # Python dependencies
├── Dockerfile           # Container configuration
├── docker-compose.yml   # Local development setup
└── service management scripts (restart.sh, status.sh, etc.)
```

## API Documentation Scraper Structure

```
crawl/
├── scrape_chatfire_docs.py     # Full-featured scraper
├── scrape_chatfire_simple.py   # Simplified scraper (standard library only)
├── run_scraper.py             # Scraper execution script
├── requirements.txt           # Scraper dependencies
└── README.md                 # Usage instructions
```

## Architecture Principles

### Layered Architecture
- **Routers**: Handle HTTP requests, parameter parsing, response formatting
- **Services**: Implement business logic, data processing, external API calls
- **Core**: Provide foundational components (clients, config, logging)

### Configuration Management
- All settings centralized in `core/config.py` using Pydantic models
- Environment-specific configuration via `.env` files
- No hardcoded values in business logic

### Logging Strategy
- Structured logging via `core/logger.py`
- Separate log files for different components
- Log rotation and level management

### Service Management
- Shell scripts for common operations (`restart.sh`, `status.sh`, `stop.sh`)
- Docker Compose for containerized deployment
- Health checks and monitoring endpoints

## File Naming Conventions
- **Python modules**: lowercase with underscores (snake_case)
- **Configuration files**: lowercase with dots/hyphens
- **Documentation**: UPPERCASE.md for important docs, lowercase.md for others
- **Scripts**: descriptive names with .sh/.py extensions

## Key Directories to Know
- `meta-curl-api/routers/mcp/` - MCP tool implementations
- `meta-curl-api/services/` - Core business logic
- `meta-curl-api/core/` - Shared utilities and configuration
- `api_docs/` - Generated documentation output
- `.kiro/specs/` - Kiro IDE specifications and requirements