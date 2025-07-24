#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
分析API文档内容，提取正确的端点信息
"""

import asyncio
import aiohttp
import json
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

# 伪造浏览器请求头
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"'
}

async def fetch_and_parse_api_doc(session: aiohttp.ClientSession, url: str, name: str) -> Optional[Dict]:
    """获取并解析单个API文档"""
    try:
        print(f"🔍 正在分析 {name} ...")
        
        async with session.get(url, headers=BROWSER_HEADERS) as response:
            if response.status == 200:
                html_content = await response.text()
                
                # 使用BeautifulSoup解析HTML
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # 提取API信息
                api_info = extract_api_info(soup, name)
                print(f"✅ {name}: {api_info.get('method', 'POST')} {api_info.get('endpoint', 'unknown')}")
                
                return api_info
            else:
                print(f"❌ 获取 {name} 失败: HTTP {response.status}")
                return None
                
    except Exception as e:
        print(f"❌ 分析 {name} 出错: {str(e)}")
        return None

def extract_api_info(soup: BeautifulSoup, api_name: str) -> Dict:
    """从HTML内容中提取API信息"""
    api_info = {
        "name": api_name,
        "endpoint": "",
        "method": "POST",
        "headers": {},
        "parameters": {},
        "base_url": "https://api.chatfire.cn"
    }
    
    # 查找API路径的多种方式
    text_content = soup.get_text()
    
    # 方法1: 查找常见的路径模式
    path_patterns = [
        r'/v1/images/[a-zA-Z]+',  # OpenAI风格
        r'/[a-zA-Z]+/[a-zA-Z]+',  # 通用API路径
        r'POST\s+(/[^\s]+)',      # POST后跟路径
        r'接口路径[：:]\s*(/[^\s]+)',
        r'URL[：:]\s*[^\s]*(/[^\s]+)',
        r'"path":\s*"([^"]+)"',
        r"'path':\s*'([^']+)'",
    ]
    
    for pattern in path_patterns:
        matches = re.findall(pattern, text_content, re.IGNORECASE)
        if matches:
            potential_path = matches[0]
            # 验证路径是否合理
            if len(potential_path) > 1 and potential_path.startswith('/'):
                api_info["endpoint"] = potential_path
                break
    
    # 如果没有找到路径，根据API名称推断
    if not api_info["endpoint"]:
        api_info["endpoint"] = guess_endpoint_from_name(api_name)
    
    # 查找HTTP方法
    method_patterns = [
        r'\b(POST|GET|PUT|DELETE)\b',
        r'"method":\s*"(POST|GET|PUT|DELETE)"',
        r"'method':\s*'(POST|GET|PUT|DELETE)'"
    ]
    
    for pattern in method_patterns:
        matches = re.findall(pattern, text_content, re.IGNORECASE)
        if matches:
            api_info["method"] = matches[0].upper()
            break
    
    # 查找请求参数
    try:
        # 查找JSON示例
        json_patterns = [
            r'\{[^{}]*"prompt"[^{}]*\}',
            r'\{[^{}]*"text"[^{}]*\}',
            r'\{[^{}]*"image"[^{}]*\}',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text_content, re.DOTALL)
            if matches:
                try:
                    sample_json = json.loads(matches[0])
                    api_info["sample_request"] = sample_json
                    break
                except:
                    continue
    except:
        pass
    
    return api_info

def guess_endpoint_from_name(api_name: str) -> str:
    """根据API名称推断端点路径"""
    name_to_endpoint = {
        "GPT图像生成": "/v1/images/generations",
        "Recraft图像生成": "/recraft/v1/images/generations", 
        "Seedream图像生成": "/seedream/v1/images/generations",
        "StableDiffusion图像生成": "/stable-diffusion/v1/images/generations",
        "虚拟换衣": "/virtual-try-on/v1/images/generations",
        "海螺图片": "/hailuo/v1/images/generations",
        "Doubao图片生成": "/doubao/v1/images/generations"
    }
    
    return name_to_endpoint.get(api_name, "/unknown/generate")

async def main():
    """主函数"""
    print("🚀 开始分析API文档...")
    
    # API文档列表
    api_docs = [
        ("GPT图像生成", "https://apifox.com/apidoc/docs-site/3916055/289170412e0.md"),
        ("Recraft图像生成", "https://apifox.com/apidoc/docs-site/3916055/263578635e0.md"),
        ("Seedream图像生成", "https://apifox.com/apidoc/docs-site/3916055/285414862e0.md"),
        ("StableDiffusion图像生成", "https://apifox.com/apidoc/docs-site/3916055/229945648e0.md"),
        ("虚拟换衣", "https://apifox.com/apidoc/docs-site/3916055/226983436e0.md"),
        ("海螺图片", "https://apifox.com/apidoc/docs-site/3916055/295927715e0.md"),
        ("Doubao图片生成", "https://apifox.com/apidoc/docs-site/3916055/314646826e0.md")
    ]
    
    # 创建HTTP会话
    timeout = aiohttp.ClientTimeout(total=30)
    connector = aiohttp.TCPConnector(limit=10, limit_per_host=3)
    
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        # 串行处理每个API，避免过快请求
        api_endpoints = {}
        
        for name, url in api_docs:
            api_info = await fetch_and_parse_api_doc(session, url, name)
            if api_info:
                api_endpoints[name] = api_info
            
            # 短暂延迟避免请求过快
            await asyncio.sleep(1)
        
        # 保存结果
        with open("analyzed_api_endpoints.json", 'w', encoding='utf-8') as f:
            json.dump(api_endpoints, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 分析结果已保存到 analyzed_api_endpoints.json")
        
        # 生成更新代码
        if api_endpoints:
            generate_client_code(api_endpoints)

def generate_client_code(api_endpoints: Dict):
    """生成客户端代码更新"""
    print("\n🔧 正在生成客户端代码更新...")
    
    code_lines = []
    code_lines.append("# 根据API文档分析生成的端点更新")
    code_lines.append("# 更新 core/images_client.py 中的对应方法")
    code_lines.append("")
    
    for name, info in api_endpoints.items():
        endpoint = info.get('endpoint', '/unknown')
        method = info.get('method', 'POST')
        method_name = get_method_name(name)
        
        code_lines.append(f"# {name}")
        code_lines.append(f"async def {method_name}(self, data: Dict[str, Any]) -> Dict[str, Any]:")
        code_lines.append(f'    """{name}"""')
        code_lines.append(f'    return await self._make_request("{method}", "{endpoint}", data)')
        code_lines.append("")
    
    # 保存代码
    with open("client_code_updates.py", 'w', encoding='utf-8') as f:
        f.write('\n'.join(code_lines))
    
    print("✅ 客户端代码更新已保存到 client_code_updates.py")
    
    # 打印端点总结
    print("\n📋 API端点总结:")
    for name, info in api_endpoints.items():
        endpoint = info.get('endpoint', 'unknown')
        method = info.get('method', 'POST')
        print(f"  {name}: {method} {endpoint}")

def get_method_name(api_name: str) -> str:
    """获取方法名"""
    mapping = {
        "GPT图像生成": "gpt_generate",
        "Recraft图像生成": "recraft_generate", 
        "Seedream图像生成": "seedream_generate",
        "StableDiffusion图像生成": "stable_diffusion_create",
        "虚拟换衣": "virtual_try_on_generate",
        "海螺图片": "hailuo_generate",
        "Doubao图片生成": "doubao_generate"
    }
    return mapping.get(api_name, "unknown_generate")

if __name__ == "__main__":
    asyncio.run(main())