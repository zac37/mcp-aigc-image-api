#!/usr/bin/env python3
"""
深度分析ChatFire API文档网站
查看原始HTML内容和可能的数据结构
"""

import re
import json
from urllib.request import urlopen, Request
import ssl


def fetch_and_analyze():
    """获取并分析页面内容"""
    base_url = "https://api.chatfire.cn/docs"
    
    # SSL上下文
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        req = Request(base_url, headers=headers)
        with urlopen(req, context=ssl_context, timeout=30) as response:
            html_content = response.read().decode('utf-8', errors='ignore')
        
        print(f"页面大小: {len(html_content)} 字符")
        print("=" * 60)
        
        # 1. 查看页面的基本结构
        print("1. 页面基本结构:")
        if '<html' in html_content:
            print("  ✓ 包含HTML标签")
        if '<head' in html_content:
            print("  ✓ 包含HEAD标签")
        if '<body' in html_content:
            print("  ✓ 包含BODY标签")
        
        # 2. 查看JavaScript框架
        print("\n2. JavaScript框架检测:")
        frameworks = {
            'Vue.js': ['vue', '__vue__', 'Vue'],
            'React': ['react', 'React', '__react'],
            'Angular': ['angular', 'ng-'],
            'Nuxt': ['nuxt', '__NUXT__'],
            'Next.js': ['next', '__NEXT_DATA__'],
        }
        
        for framework, keywords in frameworks.items():
            if any(keyword in html_content for keyword in keywords):
                print(f"  ✓ 检测到 {framework}")
        
        # 3. 查看所有script标签
        print("\n3. Script标签分析:")
        script_tags = re.findall(r'<script[^>]*>(.*?)</script>', html_content, re.DOTALL)
        print(f"  发现 {len(script_tags)} 个script标签")
        
        for i, script in enumerate(script_tags):
            if script.strip():
                print(f"  Script {i+1} (长度: {len(script)} 字符):")
                # 显示前200个字符
                preview = script.strip()[:200].replace('\n', ' ')
                print(f"    {preview}...")
        
        # 4. 查看meta标签
        print("\n4. Meta标签分析:")
        meta_tags = re.findall(r'<meta[^>]*>', html_content)
        for meta in meta_tags:
            if 'name=' in meta or 'property=' in meta:
                print(f"  {meta}")
        
        # 5. 查看title和其他重要标签
        print("\n5. 重要标签:")
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content)
        if title_match:
            print(f"  标题: {title_match.group(1)}")
        
        # 6. 查看可能的API数据
        print("\n6. 寻找可能的API数据:")
        
        # 查找JSON数据
        json_patterns = [
            r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
            r'window\.__NUXT__\s*=\s*({.+?});',
            r'window\.apiData\s*=\s*({.+?});',
            r'window\.config\s*=\s*({.+?});',
            r'__NEXT_DATA__["\']>\s*({.+?})\s*</script>',
        ]
        
        for pattern in json_patterns:
            matches = re.finditer(pattern, html_content, re.DOTALL)
            for match in matches:
                data_str = match.group(1)
                print(f"  发现JSON数据: {data_str[:100]}...")
                
                try:
                    data = json.loads(data_str)
                    print(f"    成功解析JSON，包含 {len(data)} 个顶级键")
                    if isinstance(data, dict):
                        for key in list(data.keys())[:10]:  # 显示前10个键
                            print(f"      - {key}: {type(data[key]).__name__}")
                except json.JSONDecodeError as e:
                    print(f"    JSON解析失败: {e}")
        
        # 7. 查看所有URL模式
        print("\n7. URL模式分析:")
        
        # 提取所有可能的URL
        url_patterns = [
            r'href=["\']([^"\']+)["\']',
            r'src=["\']([^"\']+)["\']',
            r'action=["\']([^"\']+)["\']',
            r'url:["\']([^"\']+)["\']',
            r'"url":\s*"([^"]+)"',
        ]
        
        all_urls = set()
        for pattern in url_patterns:
            matches = re.findall(pattern, html_content)
            for url in matches:
                if url and not url.startswith('#') and not url.startswith('data:'):
                    all_urls.add(url)
        
        print(f"  发现 {len(all_urls)} 个唯一URL:")
        for url in sorted(list(all_urls))[:20]:  # 显示前20个
            print(f"    {url}")
        
        if len(all_urls) > 20:
            print(f"    ... 还有 {len(all_urls) - 20} 个URL")
        
        # 8. 查看可能的API端点
        print("\n8. 可能的API端点:")
        api_patterns = [
            r'/api/[^"\'\s]+',
            r'/docs/[^"\'\s]+',
            r'api\.chatfire\.cn[^"\'\s]*',
        ]
        
        api_endpoints = set()
        for pattern in api_patterns:
            matches = re.findall(pattern, html_content)
            for endpoint in matches:
                api_endpoints.add(endpoint)
        
        if api_endpoints:
            for endpoint in sorted(api_endpoints):
                print(f"    {endpoint}")
        else:
            print("    未发现明显的API端点")
        
        # 9. 保存原始HTML到文件（前5000字符）
        print("\n9. 保存HTML样本:")
        with open('html_sample.html', 'w', encoding='utf-8') as f:
            f.write(html_content[:5000])
        print("  已保存HTML前5000字符到 html_sample.html")
        
        # 10. 查看特定的关键词
        print("\n10. 关键词搜索:")
        keywords = ['markdown', 'export', 'download', 'format', '导出', '格式', 'api', 'docs']
        for keyword in keywords:
            count = html_content.lower().count(keyword.lower())
            if count > 0:
                print(f"  '{keyword}': 出现 {count} 次")
        
        return html_content
        
    except Exception as e:
        print(f"分析失败: {e}")
        return None


if __name__ == "__main__":
    print("ChatFire API文档深度分析")
    print("=" * 60)
    fetch_and_analyze()