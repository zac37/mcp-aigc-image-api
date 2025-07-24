#!/usr/bin/env python3
"""
分析ChatFire API文档网站结构
寻找Markdown按钮和API链接
"""

import re
import json
from urllib.parse import urljoin
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import ssl


class ApifoxAnalyzer:
    def __init__(self, base_url: str = "https://api.chatfire.cn/docs"):
        self.base_url = base_url
        
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
                    return content.decode('utf-8', errors='ignore')
                else:
                    print(f"HTTP {response.status}: {url}")
                    return ""
                    
        except Exception as e:
            print(f"获取页面失败 {url}: {e}")
            return ""
    
    def search_markdown_buttons(self, html_content: str):
        """搜索Markdown相关按钮和链接"""
        print("=== 搜索Markdown按钮 ===")
        
        # 搜索包含"markdown"关键词的文本
        markdown_text_patterns = [
            r'以Markdown格式查看',
            r'Markdown格式',
            r'markdown.*format',
            r'view.*markdown',
            r'格式化.*查看',
            r'导出.*markdown',
            r'markdown.*导出',
        ]
        
        found_markdown = False
        for pattern in markdown_text_patterns:
            matches = re.finditer(pattern, html_content, re.IGNORECASE)
            for match in matches:
                found_markdown = True
                start = max(0, match.start() - 300)
                end = min(len(html_content), match.end() + 300)
                context = html_content[start:end]
                print(f"发现Markdown文本: '{match.group()}'")
                print(f"上下文: ...{context}...")
                print("-" * 80)
        
        if not found_markdown:
            print("未发现明显的Markdown按钮文本")
        
        # 搜索可能的Markdown URL模式
        print("\n=== 搜索Markdown URL模式 ===")
        markdown_url_patterns = [
            r'href=["\']([^"\']*markdown[^"\']*)["\']',
            r'href=["\']([^"\']*\.md[^"\']*)["\']',
            r'href=["\']([^"\']*format[^"\']*)["\']',
            r'href=["\']([^"\']*export[^"\']*)["\']',
        ]
        
        found_urls = False
        for pattern in markdown_url_patterns:
            matches = re.finditer(pattern, html_content, re.IGNORECASE)
            for match in matches:
                found_urls = True
                url = match.group(1)
                full_url = urljoin(self.base_url, url)
                print(f"发现可能的Markdown URL: {full_url}")
        
        if not found_urls:
            print("未发现明显的Markdown URL")
    
    def extract_navigation_structure(self, html_content: str):
        """提取导航结构"""
        print("\n=== 分析导航结构 ===")
        
        # 寻找可能的导航区域
        nav_patterns = [
            (r'<nav[^>]*>(.*?)</nav>', "nav标签"),
            (r'<div[^>]*class=["\'][^"\']*(?:nav|sidebar|menu|toc)[^"\']*["\'][^>]*>(.*?)</div>', "导航div"),
            (r'<aside[^>]*>(.*?)</aside>', "aside标签"),
            (r'<ul[^>]*class=["\'][^"\']*(?:nav|menu|list)[^"\']*["\'][^>]*>(.*?)</ul>', "导航列表"),
        ]
        
        all_links = []
        
        for pattern, desc in nav_patterns:
            matches = re.finditer(pattern, html_content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                nav_content = match.group(1)
                print(f"\n发现{desc} (内容长度: {len(nav_content)} 字符)")
                
                # 从导航内容中提取链接
                links = re.findall(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>', nav_content)
                
                nav_links = []
                for href, text in links:
                    if href and not href.startswith('#') and text.strip():
                        full_url = urljoin(self.base_url, href)
                        nav_links.append((text.strip(), full_url))
                        all_links.append((text.strip(), full_url))
                
                if nav_links:
                    print(f"  提取到 {len(nav_links)} 个链接:")
                    for text, url in nav_links[:10]:  # 只显示前10个
                        print(f"    {text} -> {url}")
                    if len(nav_links) > 10:
                        print(f"    ... 还有 {len(nav_links) - 10} 个链接")
        
        return all_links
    
    def analyze_page_scripts(self, html_content: str):
        """分析页面中的JavaScript，寻找API数据"""
        print("\n=== 分析页面脚本 ===")
        
        # 寻找可能包含API数据的脚本
        script_patterns = [
            r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
            r'window\.__NUXT__\s*=\s*({.+?});',
            r'window\.apiData\s*=\s*({.+?});',
            r'const\s+apiList\s*=\s*(\[.+?\]);',
            r'var\s+docs\s*=\s*({.+?});',
        ]
        
        for pattern in script_patterns:
            matches = re.finditer(pattern, html_content, re.DOTALL)
            for match in matches:
                try:
                    data_str = match.group(1)
                    print(f"发现脚本数据: {data_str[:200]}...")
                    
                    # 尝试解析JSON
                    try:
                        data = json.loads(data_str)
                        self.analyze_json_structure(data)
                    except json.JSONDecodeError:
                        print("  无法解析为JSON")
                        
                except Exception as e:
                    print(f"  分析脚本数据时出错: {e}")
    
    def analyze_json_structure(self, data, path="", max_depth=3):
        """分析JSON结构，寻找API相关信息"""
        if max_depth <= 0:
            return
        
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                
                # 寻找可能包含API信息的键
                if any(keyword in key.lower() for keyword in ['api', 'docs', 'routes', 'pages', 'menu', 'nav']):
                    print(f"  发现可能的API数据键: {current_path}")
                    if isinstance(value, (list, dict)):
                        print(f"    类型: {type(value).__name__}, 长度: {len(value) if hasattr(value, '__len__') else 'N/A'}")
                        
                        # 如果是列表，显示前几个元素
                        if isinstance(value, list) and value:
                            print(f"    示例元素: {value[0] if len(value) > 0 else 'None'}")
                
                # 递归分析
                if isinstance(value, (dict, list)):
                    self.analyze_json_structure(value, current_path, max_depth - 1)
        
        elif isinstance(data, list):
            for i, item in enumerate(data[:5]):  # 只分析前5个元素
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                if isinstance(item, (dict, list)):
                    self.analyze_json_structure(item, current_path, max_depth - 1)
    
    def extract_all_links(self, html_content: str):
        """提取页面中的所有链接"""
        print("\n=== 提取所有链接 ===")
        
        # 提取所有a标签链接
        all_links = re.findall(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>', html_content)
        
        # 过滤和分类链接
        api_links = []
        doc_links = []
        other_links = []
        
        for href, text in all_links:
            if not href or href.startswith('#'):
                continue
                
            full_url = urljoin(self.base_url, href)
            text = text.strip()
            
            if not text:
                continue
            
            # 分类链接
            if any(keyword in text.lower() or keyword in href.lower() 
                   for keyword in ['api', '接口', '创建', '获取', '任务', '图像', '视频', '语音']):
                api_links.append((text, full_url))
            elif any(keyword in text.lower() or keyword in href.lower() 
                     for keyword in ['doc', '文档', 'markdown', '格式']):
                doc_links.append((text, full_url))
            else:
                other_links.append((text, full_url))
        
        print(f"API相关链接 ({len(api_links)} 个):")
        for text, url in api_links[:15]:
            print(f"  {text} -> {url}")
        
        print(f"\n文档相关链接 ({len(doc_links)} 个):")
        for text, url in doc_links:
            print(f"  {text} -> {url}")
        
        print(f"\n其他链接: {len(other_links)} 个")
        
        return api_links, doc_links, other_links
    
    def full_analysis(self):
        """完整分析"""
        print("ChatFire API文档网站结构分析")
        print("=" * 60)
        
        html_content = self.fetch_page(self.base_url)
        if not html_content:
            print("无法获取页面内容")
            return
        
        print(f"页面大小: {len(html_content)} 字符")
        
        # 1. 搜索Markdown按钮
        self.search_markdown_buttons(html_content)
        
        # 2. 分析导航结构
        nav_links = self.extract_navigation_structure(html_content)
        
        # 3. 分析页面脚本
        self.analyze_page_scripts(html_content)
        
        # 4. 提取所有链接
        api_links, doc_links, other_links = self.extract_all_links(html_content)
        
        # 5. 总结
        print("\n" + "=" * 60)
        print("分析总结:")
        print(f"- 导航链接: {len(nav_links)} 个")
        print(f"- API链接: {len(api_links)} 个") 
        print(f"- 文档链接: {len(doc_links)} 个")
        print(f"- 其他链接: {len(other_links)} 个")
        
        return {
            'nav_links': nav_links,
            'api_links': api_links,
            'doc_links': doc_links,
            'other_links': other_links
        }


def main():
    analyzer = ApifoxAnalyzer()
    results = analyzer.full_analysis()
    
    # 保存结果到文件
    with open('analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n分析结果已保存到 analysis_results.json")


if __name__ == "__main__":
    main()