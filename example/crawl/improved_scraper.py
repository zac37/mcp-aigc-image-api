#!/usr/bin/env python3
"""
ChatFire API Documentation Scraper - Improved Version
改进版API文档抓取器，针对ChatFire网站结构优化
"""

import time
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Optional
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import ssl


class ImprovedDocsScraper:
    def __init__(self, base_url: str = "https://api.chatfire.cn/docs", output_dir: str = "../api_docs"):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.visited_urls: Set[str] = set()
        
        # 确保输出目录存在
        self.output_dir.mkdir(exist_ok=True)
        
        # SSL上下文
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def fetch_page(self, url: str) -> str:
        """获取页面内容"""
        try:
            req = Request(url, headers=self.headers)
            
            with urlopen(req, context=self.ssl_context, timeout=30) as response:
                if response.status == 200:
                    content = response.read()
                    
                    # 尝试不同的编码
                    for encoding in ['utf-8', 'gbk', 'gb2312']:
                        try:
                            return content.decode(encoding)
                        except UnicodeDecodeError:
                            continue
                    
                    # 如果都失败，使用错误忽略模式
                    return content.decode('utf-8', errors='ignore')
                else:
                    print(f"HTTP {response.status}: {url}")
                    return ""
                    
        except (URLError, HTTPError) as e:
            print(f"网络错误 {url}: {e}")
            return ""
        except Exception as e:
            print(f"未知错误 {url}: {e}")
            return ""
    
    def extract_api_content(self, html: str, url: str) -> Dict[str, str]:
        """提取API文档内容 - 针对ChatFire网站优化"""
        
        # 尝试从HTML中提取JSON数据
        json_data = self.extract_json_data(html)
        if json_data:
            return self.parse_json_content(json_data, url)
        
        # 如果没有JSON数据，尝试解析HTML
        return self.parse_html_content(html, url)
    
    def extract_json_data(self, html: str) -> Optional[Dict]:
        """从HTML中提取JSON配置数据"""
        # 查找常见的JSON数据模式
        patterns = [
            r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
            r'window\.__NUXT__\s*=\s*({.+?});',
            r'__NEXT_DATA__["\']>\s*({.+?})\s*</script>',
            r'data-page["\']>\s*({.+?})\s*</script>',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        return None
    
    def parse_json_content(self, json_data: Dict, url: str) -> Dict[str, str]:
        """解析JSON数据提取API信息"""
        content_parts = []
        title = "API文档"
        
        # 递归搜索JSON中的有用信息
        def extract_from_json(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in ['title', 'name', 'summary']:
                        nonlocal title
                        if isinstance(value, str) and value.strip():
                            title = value.strip()
                    
                    elif key in ['description', 'content', 'body', 'text']:
                        if isinstance(value, str) and value.strip():
                            content_parts.append(f"## {key.title()}\n{value.strip()}")
                    
                    elif key in ['parameters', 'params']:
                        if isinstance(value, (list, dict)):
                            content_parts.append(self.format_parameters(value))
                    
                    elif key in ['examples', 'example']:
                        if isinstance(value, (list, dict, str)):
                            content_parts.append(self.format_examples(value))
                    
                    else:
                        extract_from_json(value, f"{path}.{key}" if path else key)
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    extract_from_json(item, f"{path}[{i}]" if path else f"[{i}]")
        
        extract_from_json(json_data)
        
        return {
            'title': title,
            'content': '\n\n'.join(content_parts) if content_parts else "暂无详细内容",
            'url': url
        }
    
    def parse_html_content(self, html: str, url: str) -> Dict[str, str]:
        """解析HTML内容"""
        # 简单的HTML解析，提取文本内容
        
        # 移除脚本和样式
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # 提取标题
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else "API文档"
        
        # 提取主要内容
        content_patterns = [
            r'<main[^>]*>(.*?)</main>',
            r'<article[^>]*>(.*?)</article>',
            r'<div[^>]*class=["\'][^"\']*content[^"\']*["\'][^>]*>(.*?)</div>',
            r'<div[^>]*id=["\']content["\'][^>]*>(.*?)</div>',
        ]
        
        content = ""
        for pattern in content_patterns:
            match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1)
                break
        
        if not content:
            # 如果找不到特定内容区域，提取body内容
            body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.IGNORECASE)
            if body_match:
                content = body_match.group(1)
        
        # 清理HTML标签，保留文本
        content = re.sub(r'<[^>]+>', ' ', content)
        content = re.sub(r'\s+', ' ', content).strip()
        
        return {
            'title': title,
            'content': content if content else "暂无详细内容",
            'url': url
        }
    
    def format_parameters(self, params) -> str:
        """格式化参数信息"""
        if isinstance(params, dict):
            lines = ["## 参数"]
            for name, info in params.items():
                if isinstance(info, dict):
                    param_type = info.get('type', '未知')
                    required = "必需" if info.get('required', False) else "可选"
                    description = info.get('description', '无描述')
                    lines.append(f"- **{name}** ({param_type}, {required}): {description}")
                else:
                    lines.append(f"- **{name}**: {info}")
            return '\n'.join(lines)
        
        elif isinstance(params, list):
            lines = ["## 参数"]
            for param in params:
                if isinstance(param, dict):
                    name = param.get('name', '未知参数')
                    param_type = param.get('type', '未知')
                    required = "必需" if param.get('required', False) else "可选"
                    description = param.get('description', '无描述')
                    lines.append(f"- **{name}** ({param_type}, {required}): {description}")
                else:
                    lines.append(f"- {param}")
            return '\n'.join(lines)
        
        return f"## 参数\n{params}"
    
    def format_examples(self, examples) -> str:
        """格式化示例信息"""
        lines = ["## 示例"]
        
        if isinstance(examples, str):
            lines.append(f"```\n{examples}\n```")
        elif isinstance(examples, list):
            for i, example in enumerate(examples, 1):
                lines.append(f"### 示例 {i}")
                if isinstance(example, str):
                    lines.append(f"```\n{example}\n```")
                else:
                    lines.append(f"```json\n{json.dumps(example, indent=2, ensure_ascii=False)}\n```")
        elif isinstance(examples, dict):
            lines.append(f"```json\n{json.dumps(examples, indent=2, ensure_ascii=False)}\n```")
        
        return '\n'.join(lines)
    
    def categorize_content(self, title: str, url: str, content: str) -> str:
        """内容分类"""
        title_lower = title.lower()
        url_lower = url.lower()
        content_lower = content.lower()
        
        categories = {
            '图像生成': ['image', 'picture', 'photo', 'flux', 'stable', 'midjourney', '图像', '图片', '生成', 'generate', 'cogview', 'recraft'],
            '视频生成': ['video', 'movie', 'clip', '视频', '影片', 'cogvideo', 'runway', 'pika', 'vidu', 'kling'],
            '语音处理': ['audio', 'voice', 'speech', 'tts', '语音', '音频', '合成', '克隆', 'elevenlabs', 'fish'],
            '文件处理': ['file', 'upload', 'download', '文件', '上传', '下载', 'pdf', 'document', 'ocr'],
            '任务管理': ['task', 'job', 'queue', '任务', '队列', '状态', 'status', '获取', '创建'],
            '内容审核': ['moderation', 'review', 'check', '审核', '检查', '过滤'],
            '文本处理': ['text', 'translate', 'ocr', '文本', '翻译', '识别', 'markdown'],
            '嵌入向量': ['embedding', 'vector', '嵌入', '向量', '相似'],
            '系统接口': ['api', 'system', 'config', '系统', '配置', '接口', 'key'],
        }
        
        for category, keywords in categories.items():
            if any(keyword in title_lower or keyword in url_lower or keyword in content_lower 
                   for keyword in keywords):
                return category
        
        return '其他'
    
    def save_content(self, category: str, title: str, content: str, url: str):
        """保存内容"""
        category_dir = self.output_dir / category
        category_dir.mkdir(exist_ok=True)
        
        # 清理文件名
        safe_filename = re.sub(r'[^\w\s-]', '', title).strip()
        safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
        
        if not safe_filename:
            safe_filename = f"page-{len(self.visited_urls)}"
        
        file_path = category_dir / f"{safe_filename}.md"
        
        # 构建markdown内容
        full_content = f"# {title}\n\n"
        full_content += f"**URL**: {url}\n\n"
        full_content += content
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            print(f"保存: {file_path}")
            return True
        except Exception as e:
            print(f"保存失败 {file_path}: {e}")
            return False
    
    def analyze_page_structure(self, test_url: str = None):
        """分析页面结构，寻找Markdown按钮和API链接"""
        if not test_url:
            test_url = self.base_url
        
        print(f"分析页面: {test_url}")
        
        html_content = self.fetch_page(test_url)
        if not html_content:
            print("无法获取页面内容")
            return
        
        print(f"页面大小: {len(html_content)} 字符")
        
        # 寻找Markdown按钮
        print("\n=== 寻找Markdown按钮 ===")
        markdown_patterns = [
            r'以Markdown格式查看',
            r'markdown.*format',
            r'view.*markdown',
            r'markdown.*view',
            r'格式化.*查看',
            r'查看.*格式',
        ]
        
        for pattern in markdown_patterns:
            matches = re.finditer(pattern, html_content, re.IGNORECASE)
            for match in matches:
                start = max(0, match.start() - 200)
                end = min(len(html_content), match.end() + 200)
                context = html_content[start:end]
                print(f"发现模式 '{pattern}':")
                print(f"上下文: ...{context}...")
                print("-" * 50)
        
        # 寻找可能的Markdown URL
        print("\n=== 寻找Markdown相关URL ===")
        markdown_url_patterns = [
            r'href=["\']([^"\']*markdown[^"\']*)["\']',
            r'href=["\']([^"\']*\.md[^"\']*)["\']',
            r'href=["\']([^"\']*format[^"\']*)["\']',
        ]
        
        for pattern in markdown_url_patterns:
            matches = re.finditer(pattern, html_content, re.IGNORECASE)
            for match in matches:
                url = match.group(1)
                print(f"发现Markdown URL: {url}")
        
        # 分析左侧导航栏
        print("\n=== 分析左侧导航栏 ===")
        self.extract_navigation_links(html_content)
        
        # 寻找所有API相关链接
        print("\n=== 寻找所有API链接 ===")
        self.extract_all_api_links(html_content)
    
    def extract_navigation_links(self, html_content: str):
        """提取左侧导航栏的链接"""
        # 寻找导航相关的HTML结构
        nav_patterns = [
            r'<nav[^>]*>(.*?)</nav>',
            r'<div[^>]*class=["\'][^"\']*nav[^"\']*["\'][^>]*>(.*?)</div>',
            r'<div[^>]*class=["\'][^"\']*sidebar[^"\']*["\'][^>]*>(.*?)</div>',
            r'<div[^>]*class=["\'][^"\']*menu[^"\']*["\'][^>]*>(.*?)</div>',
            r'<aside[^>]*>(.*?)</aside>',
        ]
        
        for pattern in nav_patterns:
            matches = re.finditer(pattern, html_content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                nav_content = match.group(1)
                print(f"发现导航区域 (长度: {len(nav_content)} 字符)")
                
                # 从导航区域提取链接
                links = re.findall(r'href=["\']([^"\']+)["\'][^>]*>([^<]+)', nav_content)
                for href, text in links:
                    if href and not href.startswith('#'):
                        full_url = urljoin(self.base_url, href)
                        print(f"  导航链接: {text.strip()} -> {full_url}")
    
    def extract_all_api_links(self, html_content: str):
        """提取所有可能的API链接"""
        # 提取所有链接
        all_links = re.findall(r'href=["\']([^"\']+)["\'][^>]*>([^<]*)', html_content)
        
        api_links = []
        for href, text in all_links:
            if href and not href.startswith('#'):
                full_url = urljoin(self.base_url, href)
                
                # 过滤API相关链接
                if (self.base_url in full_url and 
                    any(keyword in text.lower() or keyword in href.lower() 
                        for keyword in ['api', '接口', '创建', '获取', '任务', '图像', '视频', '语音', '文件'])):
                    api_links.append((text.strip(), full_url))
        
        print(f"发现 {len(api_links)} 个API相关链接:")
        for text, url in api_links[:20]:  # 只显示前20个
            print(f"  {text} -> {url}")
        
        if len(api_links) > 20:
            print(f"  ... 还有 {len(api_links) - 20} 个链接")
        
        return api_links
    
    def search_markdown_buttons(self, html_content: str):
        """专门搜索Markdown按钮"""
        print("\n=== 详细搜索Markdown按钮 ===")
        
        # 搜索包含"markdown"的所有HTML元素
        markdown_elements = re.finditer(r'<[^>]*markdown[^>]*>.*?</[^>]*>', html_content, re.IGNORECASE | re.DOTALL)
        for match in markdown_elements:
            element = match.group(0)
            print(f"Markdown元素: {element[:200]}...")
        
        # 搜索按钮相关元素
        button_patterns = [
            r'<button[^>]*>.*?markdown.*?</button>',
            r'<a[^>]*>.*?markdown.*?</a>',
            r'<div[^>]*>.*?markdown.*?</div>',
        ]
        
        for pattern in button_patterns:
            matches = re.finditer(pattern, html_content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                button = match.group(0)
                print(f"按钮元素: {button}")
                
                # 提取href属性
                href_match = re.search(r'href=["\']([^"\']+)["\']', button)
                if href_match:
                    href = href_match.group(1)
                    print(f"  -> 链接: {href}")
    
    def test_single_page(self, test_url: str = None):
        """测试单个页面的抓取效果"""
        if not test_url:
            test_url = self.base_url
        
        print(f"测试页面: {test_url}")
        
        html_content = self.fetch_page(test_url)
        if not html_content:
            print("无法获取页面内容")
            return
        
        # 搜索Markdown按钮
        self.search_markdown_buttons(html_content)
        
        # 分析页面结构
        print("\n页面结构分析:")
        if 'window.__INITIAL_STATE__' in html_content:
            print("- 发现 window.__INITIAL_STATE__")
        if 'window.__NUXT__' in html_content:
            print("- 发现 window.__NUXT__")
        if '<script' in html_content:
            script_count = html_content.count('<script')
            print(f"- 发现 {script_count} 个script标签")
        
        # 提取内容
        content_data = self.extract_api_content(html_content, test_url)
        
        print(f"\n提取结果:")
        print(f"标题: {content_data['title']}")
        print(f"内容长度: {len(content_data['content'])} 字符")
        print(f"内容预览: {content_data['content'][:200]}...")
        
        # 分类
        category = self.categorize_content(
            content_data['title'], 
            test_url, 
            content_data['content']
        )
        print(f"分类: {category}")
        
        # 保存测试结果
        self.save_content(
            f"测试-{category}",
            content_data['title'],
            content_data['content'],
            test_url
        )


def main():
    scraper = ImprovedDocsScraper()
    
    print("ChatFire API文档抓取器 - 改进版")
    print("=" * 50)
    
    # 测试主页
    scraper.test_single_page()
    
    # 测试一个具体的API页面
    print("\n" + "="*50)
    scraper.test_single_page("https://api.chatfire.cn/docs/6861445m0")


if __name__ == "__main__":
    main()