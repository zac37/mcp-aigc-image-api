#!/usr/bin/env python3
"""
Configuration management for the API documentation scraper
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import os
from pathlib import Path


@dataclass
class ScraperConfig:
    """Configuration class for the scraper with all configurable parameters"""
    
    # Basic settings
    base_url: str = "https://api.chatfire.cn/docs"
    output_directory: str = "../api_docs"
    
    # Rate limiting and retry settings
    rate_limit_delay: float = 1.0  # seconds between requests
    max_retries: int = 3
    request_timeout: int = 30
    
    # Content processing settings
    include_images: bool = True
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    # Browser settings for Selenium (if used)
    headless_browser: bool = True
    browser_timeout: int = 30
    
    # Categories mapping for Chinese API documentation
    categories_mapping: Dict[str, str] = None
    
    def __post_init__(self):
        """Initialize default categories mapping if not provided"""
        if self.categories_mapping is None:
            self.categories_mapping = {
                '用户管理': ['user', 'account', 'profile', 'auth', 'login', 'register', '用户', '账户', 'member'],
                '消息管理': ['message', 'chat', 'conversation', 'msg', '消息', '聊天', 'send', 'receive'],
                '文件管理': ['file', 'upload', 'download', 'media', 'attachment', '文件', '上传', 'image'],
                '群组管理': ['group', 'team', 'channel', 'room', '群组', '团队', '频道', 'workspace'],
                '配置管理': ['config', 'setting', 'preference', 'option', '配置', '设置', 'webhook'],
                '统计分析': ['stat', 'analytics', 'report', 'metric', '统计', '分析', '报告', 'dashboard'],
                '系统管理': ['system', 'admin', 'manage', 'control', '系统', '管理', 'api'],
                'AI功能': ['ai', 'bot', 'assistant', 'intelligent', '智能', '机器人', 'model'],
                '接口文档': ['api', 'endpoint', 'reference', 'doc', '接口', '文档'],
            }
    
    @classmethod
    def from_env(cls) -> 'ScraperConfig':
        """Create configuration from environment variables"""
        return cls(
            base_url=os.getenv('SCRAPER_BASE_URL', cls.base_url),
            output_directory=os.getenv('SCRAPER_OUTPUT_DIR', cls.output_directory),
            rate_limit_delay=float(os.getenv('SCRAPER_RATE_LIMIT', cls.rate_limit_delay)),
            max_retries=int(os.getenv('SCRAPER_MAX_RETRIES', cls.max_retries)),
            request_timeout=int(os.getenv('SCRAPER_TIMEOUT', cls.request_timeout)),
            include_images=os.getenv('SCRAPER_INCLUDE_IMAGES', 'true').lower() == 'true',
            headless_browser=os.getenv('SCRAPER_HEADLESS', 'true').lower() == 'true',
        )
    
    def validate(self) -> List[str]:
        """Validate configuration parameters and return list of errors"""
        errors = []
        
        if not self.base_url:
            errors.append("base_url cannot be empty")
        
        if not self.output_directory:
            errors.append("output_directory cannot be empty")
        
        if self.rate_limit_delay < 0:
            errors.append("rate_limit_delay must be non-negative")
        
        if self.max_retries < 0:
            errors.append("max_retries must be non-negative")
        
        if self.request_timeout <= 0:
            errors.append("request_timeout must be positive")
        
        return errors
    
    def ensure_output_directory(self) -> Path:
        """Ensure output directory exists and return Path object"""
        output_path = Path(self.output_directory)
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path