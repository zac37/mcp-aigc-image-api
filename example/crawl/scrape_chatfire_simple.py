#!/usr/bin/env python3
"""
ChatFire API Documentation Scraper (简化版)
抓取 https://api.chatfire.cn/docs 的API文档并按分类存储为markdown格式
使用标准库减少依赖
"""

import asyncio
import os
import re
import json
import time
from urllib.parse import urljoin, urlparse
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from html.parser import HTMLParser
from typing import Dict, List, Set
import ssl

class MarkdownConverter(HTMLParser):
    """HTML到Markdown转换器"""
    
    def __init__(self):
        super().__init__()
        self.markdown_lines = []
        self.current_tag = None
        self.list_depth = 0
        self.in_pre = False
        self.in_code = False
        self.table_rows = []
        self.in_table = False
        
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        
        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(tag[1])
            self.markdown_lines.append('#' * level + ' ')
        elif tag == 'p':
            self.markdown_lines.append('\n')
        elif tag in ['ul', 'ol']:
            self.list_depth += 1
        elif tag == 'li':
            self.markdown_lines.append('- ')
        elif tag == 'pre':
            self.markdown_lines.append('\n```\n')
            self.in_pre = True
        elif tag == 'code' and not self.in_pre:
            self.markdown_lines.append('`')
            self.in_code = True
        elif tag == 'strong' or tag == 'b':
            self.markdown_lines.append('**')
        elif tag == 'em' or tag == 'i':
            self.markdown_lines.append('*')
        elif tag == 'a':
            href = dict(attrs).get('href', '')
            if href:
                self.markdown_lines.append('[')
        elif tag == 'table':
            self.in_table = True
            self.table_rows = []
        elif tag == 'tr' and self.in_table:
            self.table_rows.append([])
    
    def handle_endtag(self, tag):
        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.markdown_lines.append('\n\n')
        elif tag == 'p':
            self.markdown_lines.append('\n\n')
        elif tag in ['ul', 'ol']:
            self.list_depth -= 1
            if self.list_depth == 0:
                self.markdown_lines.append('\n')
        elif tag == 'li':
            self.markdown_lines.append('\n')
        elif tag == 'pre':
            self.markdown_lines.append('\n```\n\n')
            self.in_pre = False
        elif tag == 'code' and self.in_code:
            self.markdown_lines.append('`')
            self.in_code = False
        elif tag == 'strong' or tag == 'b':
            self.markdown_lines.append('**')
        elif tag == 'em' or tag == 'i':
            self.markdown_lines.append('*')
        elif tag == 'table':
            self.in_table = False
            if self.table_rows:
                self.process_table()
        
        self.current_tag = None
    
    def handle_data(self, data):
        if data.strip():
            self.markdown_lines.append(data.strip())
            if self.in_table and self.table_rows:
                self.table_rows[-1].append(data.strip())
    
    def process_table(self):
        """处理表格数据"""
        if not self.table_rows:
            return
            
        # 表头
        if self.table_rows:
            header = self.table_rows[0]
            self.markdown_lines.append('| ' + ' | '.join(header) + ' |\n')
            self.markdown_lines.append('| ' + ' | '.join(['---'] * len(header)) + ' |\n')
            
            # 表格内容
            for row in self.table_rows[1:]:
                if row:
                    self.markdown_lines.append('| ' + ' | '.join(row) + ' |\n')
            
        self.markdown_lines.append('\n')
    
    def get_markdown(self):
        """获取转换后的Markdown内容"""
        return ''.join(self.markdown_lines)

class ChatFireDocsScraper:
    def __init__(self, base_url: str = "https://api.chatfire.cn/docs", output_dir: str = "../api_docs"):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.visited_urls: Set[str] = set()
        
        # 确保输出目录存在
        self.output_dir.mkdir(exist_ok=True)
        
        # SSL上下文（忽略证书验证）
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
    def fetch_page(self, url: str) -> str:
        """获取页面内容"""
        try:
            req = Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            with urlopen(req, context=self.ssl_context, timeout=30) as response:
                if response.status == 200:
                    return response.read().decode('utf-8', errors='ignore')
                else:
                    print(f"Failed to fetch {url}: HTTP {response.status}")
                    return ""
                    
        except (URLError, HTTPError) as e:
            print(f"Error fetching {url}: {e}")
            return ""
        except Exception as e:
            print(f"Unexpected error fetching {url}: {e}")
            return ""
    
    def extract_links(self, html_content: str, base_url: str) -> List[Dict[str, str]]:
        """从HTML中提取链接"""
        links = []
        
        # 简单的正则提取链接
        link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
        matches = re.findall(link_pattern, html_content, re.IGNORECASE)
        
        for href, text in matches:
            if href and text.strip() and not href.startswith('#'):
                # 转换为绝对URL
                absolute_url = urljoin(base_url, href)
                
                # 过滤掉外部链接
                if absolute_url.startswith(base_url.split('/docs')[0]):
                    links.append({
                        'title': text.strip(),
                        'url': absolute_url
                    })
        
        return links
    
    def categorize_link(self, title: str, url: str) -> str:
        """根据标题和URL对API进行分类"""
        title_lower = title.lower()
        url_lower = url.lower()
        
        # 常见的API分类模式
        categories = {
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
        
        for category, keywords in categories.items():
            if any(keyword in title_lower or keyword in url_lower for keyword in keywords):
                return category
        
        return '其他'
    
    def html_to_markdown(self, html_content: str) -> str:
        """将HTML内容转换为Markdown格式"""
        converter = MarkdownConverter()
        
        # 提取主要内容区域
        content_patterns = [
            r'<main[^>]*>(.*?)</main>',
            r'<article[^>]*>(.*?)</article>',
            r'<div[^>]*class=["\'][^"\']*content[^"\']*["\'][^>]*>(.*?)</div>',
            r'<div[^>]*id=["\']content["\'][^>]*>(.*?)</div>',
        ]
        
        main_content = html_content
        for pattern in content_patterns:
            match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
            if match:
                main_content = match.group(1)
                break
        
        # 清理HTML
        main_content = re.sub(r'<script[^>]*>.*?</script>', '', main_content, flags=re.DOTALL)
        main_content = re.sub(r'<style[^>]*>.*?</style>', '', main_content, flags=re.DOTALL)
        
        converter.feed(main_content)
        return converter.get_markdown()
    
    def save_markdown_file(self, category: str, title: str, content: str):
        """保存Markdown文件"""
        # 创建分类目录
        category_dir = self.output_dir / category
        category_dir.mkdir(exist_ok=True)
        
        # 清理文件名
        safe_filename = re.sub(r'[^\w\s-]', '', title).strip()
        safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
        
        if not safe_filename:
            safe_filename = "unnamed"
        
        file_path = category_dir / f"{safe_filename}.md"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n")
                f.write(content)
            
            print(f"Saved: {file_path}")
        except Exception as e:
            print(f"Error saving {file_path}: {e}")
    
    def scrape_all(self):
        """开始抓取所有文档"""
        print(f"开始抓取 {self.base_url} 的API文档...")
        
        # 获取主页面
        main_content = self.fetch_page(self.base_url)
        if not main_content:
            print("无法获取主页面内容")
            return
        
        # 提取所有链接
        links = self.extract_links(main_content, self.base_url)
        print(f"发现 {len(links)} 个链接")
        
        # 按分类组织链接
        categorized_links = {}
        for link in links:
            category = self.categorize_link(link['title'], link['url'])
            if category not in categorized_links:
                categorized_links[category] = []
            categorized_links[category].append(link)
        
        print(f"发现 {len(categorized_links)} 个分类:")
        for category, links in categorized_links.items():
            print(f"  {category}: {len(links)} 个页面")
        
        # 抓取每个页面
        total_pages = 0
        for category, links in categorized_links.items():
            print(f"\n处理分类: {category}")
            
            for link_info in links:
                url = link_info['url']
                title = link_info['title']
                
                if url in self.visited_urls:
                    continue
                
                self.visited_urls.add(url)
                print(f"  抓取: {title}")
                
                page_content = self.fetch_page(url)
                if page_content:
                    markdown_content = self.html_to_markdown(page_content)
                    self.save_markdown_file(category, title, markdown_content)
                    total_pages += 1
                
                # 添加延迟避免请求过快
                time.sleep(0.5)
        
        print(f"\n抓取完成! 共处理 {total_pages} 个页面，文档保存在 {self.output_dir} 目录中")

def main():
    scraper = ChatFireDocsScraper()
    scraper.scrape_all()

if __name__ == "__main__":
    main()