---
inclusion: always
---

# Chinese Language Support Guidelines

## Communication Language
- Always respond in Chinese when working with Chinese API documentation or Chinese-named files
- Use Chinese for explanations when discussing Chinese API services or endpoints
- Maintain bilingual approach: Chinese for user communication, English for code comments and technical documentation

## Documentation Standards
- API documentation files in `api_docs/消息管理/` use Chinese filenames and content
- Preserve original Chinese API parameter names and descriptions
- Use descriptive Chinese comments in code when working with Chinese API services
- Keep Chinese error messages from external APIs while providing English translations in logs

## File Naming Conventions
- Chinese characters are acceptable in documentation filenames (e.g., `消息管理/`, `任务状态.md`)
- Use UTF-8 encoding for all files containing Chinese content
- Maintain consistency between Chinese API documentation and corresponding code implementations

## Code Implementation
- Preserve Chinese field names in API request/response models when interfacing with Chinese services (e.g., `消息管理`, `任务状态`, `任务结果`)
- Use English for internal variable names and function names in Python code
- Handle Chinese text properly in URL encoding and JSON serialization
- Ensure proper encoding handling for Chinese characters in HTTP requests and responses

## API Integration Best Practices
- Respect original Chinese API parameter names to maintain compatibility
- Document Chinese API endpoints with both Chinese descriptions and English technical notes
- Test Chinese character handling in all API request/response cycles
- Validate UTF-8 encoding in data persistence and transmission