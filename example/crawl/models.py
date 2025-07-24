#!/usr/bin/env python3
"""
Data models for the API documentation scraper
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


@dataclass
class PageContent:
    """Model for scraped page content"""
    url: str
    title: str
    content: str
    category: str
    api_method: Optional[str] = None
    endpoint: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    last_modified: Optional[datetime] = None
    raw_html: Optional[str] = None
    
    def to_markdown(self) -> str:
        """Convert page content to markdown format"""
        lines = [f"# {self.title}\n"]
        
        if self.api_method and self.endpoint:
            lines.append(f"**方法**: {self.api_method}")
            lines.append(f"**端点**: {self.endpoint}\n")
        
        if self.parameters:
            lines.append("## 参数\n")
            for param in self.parameters:
                name = param.get('name', '')
                param_type = param.get('type', '')
                required = param.get('required', False)
                description = param.get('description', '')
                
                required_text = "必需" if required else "可选"
                lines.append(f"- **{name}** ({param_type}, {required_text}): {description}")
            lines.append("")
        
        if self.content:
            lines.append("## 详细说明\n")
            lines.append(self.content)
        
        if self.examples:
            lines.append("\n## 示例\n")
            for i, example in enumerate(self.examples, 1):
                lines.append(f"### 示例 {i}\n")
                lines.append(f"```\n{example}\n```\n")
        
        if self.last_modified:
            lines.append(f"\n---\n*最后更新: {self.last_modified.strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return '\n'.join(lines)


@dataclass
class ScrapingResult:
    """Model for scraping operation results"""
    total_pages: int = 0
    successful_pages: int = 0
    failed_pages: List[str] = field(default_factory=list)
    categories_created: List[str] = field(default_factory=list)
    output_directory: str = ""
    execution_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_pages == 0:
            return 0.0
        return (self.successful_pages / self.total_pages) * 100
    
    def add_error(self, error: str):
        """Add an error to the results"""
        self.errors.append(error)
    
    def add_failed_page(self, url: str):
        """Add a failed page URL"""
        self.failed_pages.append(url)
    
    def to_summary(self) -> str:
        """Generate a summary report"""
        lines = [
            "# 抓取结果摘要\n",
            f"**总页面数**: {self.total_pages}",
            f"**成功页面数**: {self.successful_pages}",
            f"**失败页面数**: {len(self.failed_pages)}",
            f"**成功率**: {self.success_rate:.1f}%",
            f"**创建分类数**: {len(self.categories_created)}",
            f"**输出目录**: {self.output_directory}",
            f"**执行时间**: {self.execution_time:.2f} 秒\n"
        ]
        
        if self.categories_created:
            lines.append("## 创建的分类\n")
            for category in self.categories_created:
                lines.append(f"- {category}")
            lines.append("")
        
        if self.failed_pages:
            lines.append("## 失败的页面\n")
            for url in self.failed_pages:
                lines.append(f"- {url}")
            lines.append("")
        
        if self.errors:
            lines.append("## 错误信息\n")
            for error in self.errors:
                lines.append(f"- {error}")
        
        return '\n'.join(lines)


@dataclass
class NavigationItem:
    """Model for navigation structure items"""
    title: str
    url: str
    category: str
    parent: Optional['NavigationItem'] = None
    children: List['NavigationItem'] = field(default_factory=list)
    depth: int = 0
    
    def add_child(self, child: 'NavigationItem'):
        """Add a child navigation item"""
        child.parent = self
        child.depth = self.depth + 1
        self.children.append(child)
    
    def get_all_urls(self) -> List[str]:
        """Get all URLs in this navigation tree"""
        urls = [self.url]
        for child in self.children:
            urls.extend(child.get_all_urls())
        return urls
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'title': self.title,
            'url': self.url,
            'category': self.category,
            'depth': self.depth,
            'children': [child.to_dict() for child in self.children]
        }


@dataclass
class ScrapingStats:
    """Statistics tracking for scraping operations"""
    pages_processed: int = 0
    bytes_downloaded: int = 0
    images_downloaded: int = 0
    errors_encountered: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def start_timing(self):
        """Start timing the operation"""
        self.start_time = datetime.now()
    
    def end_timing(self):
        """End timing the operation"""
        self.end_time = datetime.now()
    
    @property
    def duration(self) -> float:
        """Get duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    @property
    def pages_per_second(self) -> float:
        """Calculate pages processed per second"""
        duration = self.duration
        if duration > 0:
            return self.pages_processed / duration
        return 0.0
    
    def add_page(self, content_size: int = 0):
        """Record a processed page"""
        self.pages_processed += 1
        self.bytes_downloaded += content_size
    
    def add_image(self, image_size: int = 0):
        """Record a downloaded image"""
        self.images_downloaded += 1
        self.bytes_downloaded += image_size
    
    def add_error(self):
        """Record an error"""
        self.errors_encountered += 1