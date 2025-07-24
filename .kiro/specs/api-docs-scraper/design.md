# Design Document

## Overview

The API documentation scraper will be a Python-based tool that extracts all API documentation from https://api.chatfire.cn/docs and converts it to organized markdown files. The site appears to be a modern single-page application (SPA) that loads content dynamically via JavaScript, requiring specialized scraping techniques.

Based on research, the target site uses a documentation platform with the following characteristics:
- Dynamic content loading via JavaScript
- URL patterns like `/docs/{id}e0` for API endpoints and `/docs/{id}f0` for folders
- Hierarchical organization with folders and individual API endpoints
- Rich content including code examples, parameters, and descriptions

## Architecture

### Core Components

1. **Web Scraper Engine**
   - Selenium-based browser automation for JavaScript-heavy content
   - BeautifulSoup for HTML parsing and content extraction
   - Requests session management for efficient HTTP operations

2. **Content Parser**
   - HTML to Markdown converter
   - Code block formatter with syntax highlighting preservation
   - Table structure parser
   - Image and media handler

3. **Organization Manager**
   - Category detection and directory structure creation
   - File naming and path management
   - Duplicate content detection and handling

4. **Configuration System**
   - Target URL configuration
   - Output directory settings
   - Scraping parameters and rate limiting
   - Content filtering options

## Components and Interfaces

### 1. WebScraper Class
```python
class WebScraper:
    def __init__(self, base_url: str, output_dir: str)
    def setup_driver(self) -> webdriver.Chrome
    def discover_urls(self) -> List[str]
    def scrape_page(self, url: str) -> Dict[str, Any]
    def close(self)
```

### 2. ContentParser Class
```python
class ContentParser:
    def parse_html_to_markdown(self, html: str) -> str
    def extract_api_info(self, content: str) -> Dict[str, Any]
    def format_code_blocks(self, content: str) -> str
    def convert_tables(self, html: str) -> str
```

### 3. OrganizationManager Class
```python
class OrganizationManager:
    def __init__(self, output_dir: str)
    def create_directory_structure(self, categories: List[str])
    def determine_category(self, content: Dict[str, Any]) -> str
    def generate_filename(self, title: str, url: str) -> str
    def save_content(self, content: str, filepath: str)
```

### 4. ScraperConfig Class
```python
class ScraperConfig:
    base_url: str
    output_directory: str
    rate_limit_delay: float
    max_retries: int
    include_images: bool
    categories_mapping: Dict[str, str]
```

## Data Models

### PageContent Model
```python
@dataclass
class PageContent:
    url: str
    title: str
    content: str
    category: str
    api_method: Optional[str]
    endpoint: Optional[str]
    parameters: List[Dict[str, Any]]
    examples: List[str]
    last_modified: Optional[datetime]
```

### ScrapingResult Model
```python
@dataclass
class ScrapingResult:
    total_pages: int
    successful_pages: int
    failed_pages: List[str]
    categories_created: List[str]
    output_directory: str
    execution_time: float
```

## Error Handling

### Retry Mechanism
- Exponential backoff for failed requests
- Maximum retry attempts configurable
- Different retry strategies for different error types (network, parsing, etc.)

### Error Categories
1. **Network Errors**: Connection timeouts, DNS failures
2. **Parsing Errors**: Invalid HTML, missing expected elements
3. **File System Errors**: Permission issues, disk space
4. **Rate Limiting**: HTTP 429 responses, server overload

### Logging Strategy
- Structured logging with different levels (DEBUG, INFO, WARNING, ERROR)
- Separate log files for different components
- Progress tracking with percentage completion
- Error aggregation and reporting

## Testing Strategy

### Unit Tests
- Individual component testing (parser, scraper, organizer)
- Mock HTTP responses for consistent testing
- Edge case handling (malformed HTML, empty content)

### Integration Tests
- End-to-end scraping workflow
- File system operations
- Error handling scenarios

### Performance Tests
- Large-scale scraping simulation
- Memory usage monitoring
- Rate limiting effectiveness

## Implementation Details

### URL Discovery Strategy
1. **Initial Page Analysis**: Load the main docs page and extract navigation structure
2. **Dynamic Content Loading**: Use Selenium to trigger JavaScript execution and reveal all links
3. **URL Pattern Recognition**: Identify patterns for API endpoints vs. folder structures
4. **Recursive Discovery**: Follow folder links to discover nested content

### Content Extraction Process
1. **Page Loading**: Use Selenium WebDriver to fully load JavaScript content
2. **DOM Parsing**: Extract relevant content sections using CSS selectors
3. **Content Cleaning**: Remove navigation, ads, and non-essential elements
4. **Markdown Conversion**: Convert HTML to clean markdown format

### Category Organization Logic
```python
CATEGORY_MAPPING = {
    'Images': 'image-generation',
    'Audio': 'audio-processing', 
    'Videos': 'video-generation',
    'RAG': 'retrieval-augmented-generation',
    'Files': 'file-management',
    'Moderations': 'content-moderation',
    'AI工具': 'ai-tools',
    'Midjourney': 'midjourney-api',
    # ... additional mappings
}
```

### File Naming Convention
- Sanitize titles for filesystem compatibility
- Use kebab-case for consistency
- Include API method in filename when applicable
- Add unique identifiers to prevent conflicts

### Rate Limiting Implementation
- Configurable delay between requests (default: 1 second)
- Respect robots.txt if present
- Monitor response times and adjust delays dynamically
- Implement circuit breaker pattern for persistent failures

## Security Considerations

### Request Headers
- Use realistic User-Agent strings
- Include appropriate Accept headers
- Implement session management for consistency

### Content Validation
- Sanitize extracted content to prevent XSS in markdown
- Validate file paths to prevent directory traversal
- Limit file sizes to prevent disk space exhaustion

### Privacy and Ethics
- Respect website terms of service
- Implement reasonable rate limiting
- Avoid overwhelming the target server
- Cache responses to minimize repeated requests