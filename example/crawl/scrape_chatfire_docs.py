#!/usr/bin/env python3
"""
ChatFire API Documentation Scraper
抓取 https://api.chatfire.cn/docs 的API文档并按分类存储为markdown格式
"""

import asyncio
import aiohttp
import aiofiles
import os
import re
from urllib.parse import urljoin, urlparse
from pathlib import Path
from bs4 import BeautifulSoup
import json
from typing import Dict, List, Set
import time

class ChatFireDocsScraper:
    def __init__(self, base_url: str = "https://api.chatfire.cn/docs", output_dir: str = "../api_docs"):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.visited_urls: Set[str] = set()
        self.session = None
        
        # 确保输出目录存在
        self.output_dir.mkdir(exist_ok=True)
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_page(self, url: str) -> str:
        """获取页面内容"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    print(f"Failed to fetch {url}: HTTP {response.status}")
                    return ""
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""
    
    def extract_navigation(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """提取导航结构，识别API分类"""
        navigation = {}
        
        # 查找常见的导航元素
        nav_selectors = [
            'nav', '.sidebar', '.navigation', '.menu', '.toc',
            '#sidebar', '#navigation', '#menu', '#toc',
            '[role="navigation"]', '.nav-menu', '.api-nav'
        ]
        
        for selector in nav_selectors:
            nav_elements = soup.select(selector)
            for nav in nav_elements:
                # 提取链接
                links = nav.find_all('a', href=True)
                for link in links:
                    href = link.get('href')
                    text = link.get_text(strip=True)
                    
                    if href and text and not href.startswith('#'):
                        # 分类逻辑
                        category = self.categorize_link(text, href)
                        if category not in navigation:
                            navigation[category] = []
                        navigation[category].append({
                            'title': text,
                            'url': urljoin(self.base_url, href)
                        })
        
        return navigation
    
    def categorize_link(self, title: str, href: str) -> str:
        """根据标题和URL对API进行分类"""
        title_lower = title.lower()
        href_lower = href.lower()
        
        # 常见的API分类模式
        categories = {
            '用户管理': ['user', 'account', 'profile', 'auth', 'login', 'register', '用户', '账户'],
            '消息管理': ['message', 'chat', 'conversation', 'msg', '消息', '聊天'],
            '文件管理': ['file', 'upload', 'download', 'media', 'attachment', '文件', '上传'],
            '群组管理': ['group', 'team', 'channel', 'room', '群组', '团队', '频道'],
            '配置管理': ['config', 'setting', 'preference', 'option', '配置', '设置'],
            '统计分析': ['stat', 'analytics', 'report', 'metric', '统计', '分析', '报告'],
            '系统管理': ['system', 'admin', 'manage', 'control', '系统', '管理'],
            'AI功能': ['ai', 'bot', 'assistant', 'intelligent', '智能', '机器人'],
        }
        
        for category, keywords in categories.items():
            if any(keyword in title_lower or keyword in href_lower for keyword in keywords):
                return category
        
        return '其他'
    
    def html_to_markdown(self, soup: BeautifulSoup) -> str:
        """将HTML内容转换为Markdown格式"""
        markdown_lines = []
        
        # 提取标题
        title = soup.find(['h1', 'h2', 'title'])
        if title:
            markdown_lines.append(f"# {title.get_text(strip=True)}\n")
        
        # 处理内容区域
        content_selectors = [
            '.content', '.main-content', '.api-content', '.documentation',
            '#content', '#main-content', 'main', 'article'
        ]
        
        content_element = None
        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                break
        
        if not content_element:
            content_element = soup.find('body')
        
        if content_element:
            markdown_lines.append(self.process_element(content_element))
        
        return '\n'.join(markdown_lines)
    
    def process_element(self, element) -> str:
        """递归处理HTML元素转换为Markdown"""
        if element.name is None:  # 文本节点
            return element.string.strip() if element.string else ""
        
        text_content = ""
        tag_name = element.name.lower()
        
        if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(tag_name[1])
            text_content = f"{'#' * level} {element.get_text(strip=True)}\n\n"
        
        elif tag_name == 'p':
            text_content = f"{element.get_text(strip=True)}\n\n"
        
        elif tag_name in ['ul', 'ol']:
            items = []
            for li in element.find_all('li', recursive=False):
                items.append(f"- {li.get_text(strip=True)}")
            text_content = '\n'.join(items) + "\n\n"
        
        elif tag_name == 'code':
            text_content = f"`{element.get_text()}`"
        
        elif tag_name == 'pre':
            code_text = element.get_text()
            text_content = f"```\n{code_text}\n```\n\n"
        
        elif tag_name == 'a':
            href = element.get('href', '')
            link_text = element.get_text(strip=True)
            if href:
                text_content = f"[{link_text}]({href})"
            else:
                text_content = link_text
        
        elif tag_name in ['strong', 'b']:
            text_content = f"**{element.get_text(strip=True)}**"
        
        elif tag_name in ['em', 'i']:
            text_content = f"*{element.get_text(strip=True)}*"
        
        elif tag_name == 'table':
            text_content = self.process_table(element)
        
        else:
            # 处理子元素
            for child in element.children:
                text_content += self.process_element(child)
        
        return text_content
    
    def process_table(self, table_element) -> str:
        """处理表格元素"""
        rows = []
        
        # 处理表头
        headers = []
        thead = table_element.find('thead')
        if thead:
            header_cells = thead.find_all(['th', 'td'])
            headers = [cell.get_text(strip=True) for cell in header_cells]
            rows.append('| ' + ' | '.join(headers) + ' |')
            rows.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
        
        # 处理表格内容
        tbody = table_element.find('tbody') or table_element
        for tr in tbody.find_all('tr'):
            cells = tr.find_all(['td', 'th'])
            if cells:
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                rows.append('| ' + ' | '.join(cell_texts) + ' |')
        
        return '\n'.join(rows) + "\n\n"
    
    async def save_markdown_file(self, category: str, title: str, content: str):
        """保存Markdown文件"""
        # 创建分类目录
        category_dir = self.output_dir / category
        category_dir.mkdir(exist_ok=True)
        
        # 清理文件名
        safe_filename = re.sub(r'[^\w\s-]', '', title).strip()
        safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
        
        file_path = category_dir / f"{safe_filename}.md"
        
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(content)
        
        print(f"Saved: {file_path}")
    
    async def scrape_all(self):
        """开始抓取所有文档"""
        print(f"开始抓取 {self.base_url} 的API文档...")
        
        # 获取主页面
        main_content = await self.fetch_page(self.base_url)
        if not main_content:
            print("无法获取主页面内容")
            return
        
        soup = BeautifulSoup(main_content, 'html.parser')
        
        # 提取导航结构
        navigation = self.extract_navigation(soup)
        print(f"发现 {len(navigation)} 个分类:")
        for category, links in navigation.items():
            print(f"  {category}: {len(links)} 个页面")
        
        # 抓取每个页面
        for category, links in navigation.items():
            print(f"\n处理分类: {category}")
            
            for link_info in links:
                url = link_info['url']
                title = link_info['title']
                
                if url in self.visited_urls:
                    continue
                
                self.visited_urls.add(url)
                print(f"  抓取: {title} ({url})")
                
                page_content = await self.fetch_page(url)
                if page_content:
                    page_soup = BeautifulSoup(page_content, 'html.parser')
                    markdown_content = self.html_to_markdown(page_soup)
                    
                    await self.save_markdown_file(category, title, markdown_content)
                
                # 添加延迟避免请求过快
                await asyncio.sleep(0.5)
        
        print(f"\n抓取完成! 文档保存在 {self.output_dir} 目录中")

async def main():
    async with ChatFireDocsScraper() as scraper:
        await scraper.scrape_all()

if __name__ == "__main__":
    asyncio.run(main())