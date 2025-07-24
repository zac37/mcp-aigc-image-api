#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
获取API文档的脚本
通过伪造浏览器请求访问API文档
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Optional

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

# 需要获取的API文档URL列表
API_DOCS = [
    {
        "name": "GPT图像生成",
        "url": "https://apifox.com/apidoc/docs-site/3916055/289170412e0.md"
    },
    {
        "name": "Recraft图像生成",
        "url": "https://apifox.com/apidoc/docs-site/3916055/263578635e0.md"
    },
    {
        "name": "Seedream图像生成",
        "url": "https://apifox.com/apidoc/docs-site/3916055/285414862e0.md"
    },
    {
        "name": "StableDiffusion图像生成",
        "url": "https://apifox.com/apidoc/docs-site/3916055/229945648e0.md"
    },
    {
        "name": "虚拟换衣",
        "url": "https://apifox.com/apidoc/docs-site/3916055/226983436e0.md"
    },
    {
        "name": "海螺图片",
        "url": "https://apifox.com/apidoc/docs-site/3916055/295927715e0.md"
    },
    {
        "name": "Doubao图片生成",
        "url": "https://apifox.com/apidoc/docs-site/3916055/314646826e0.md"
    }
]

async def fetch_api_doc(session: aiohttp.ClientSession, api_info: Dict) -> Optional[Dict]:
    """获取单个API文档"""
    try:
        print(f"正在获取 {api_info['name']} 的API文档...")
        
        async with session.get(api_info['url'], headers=BROWSER_HEADERS) as response:
            if response.status == 200:
                content = await response.text()
                print(f"✅ 成功获取 {api_info['name']} 文档 ({len(content)} 字符)")
                
                # 解析文档内容，提取API端点信息
                endpoint_info = parse_api_endpoint(content, api_info['name'])
                return endpoint_info
            else:
                print(f"❌ 获取 {api_info['name']} 文档失败: HTTP {response.status}")
                return None
                
    except Exception as e:
        print(f"❌ 获取 {api_info['name']} 文档出错: {str(e)}")
        return None

def parse_api_endpoint(content: str, api_name: str) -> Dict:
    """解析API文档内容，提取端点信息"""
    # 这里需要根据实际的HTML内容来解析API端点
    # 目前先返回基本结构，后续根据实际内容调整
    endpoint_info = {
        "name": api_name,
        "endpoint": "",
        "method": "POST",
        "headers": {},
        "parameters": {},
        "raw_content_length": len(content)
    }
    
    # 尝试从内容中提取API路径
    # 通常apifox文档中会包含类似 "/v1/images/generations" 的路径
    import re
    
    # 查找API路径模式
    path_patterns = [
        r'(?:POST|GET|PUT|DELETE)\s+([/\w\-\.]+)',
        r'"path":\s*"([^"]+)"',
        r'接口路径[：:]\s*([/\w\-\.]+)',
        r'URL[：:]\s*[^\s]*([/\w\-\.]+)',
    ]
    
    for pattern in path_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            endpoint_info["endpoint"] = matches[0]
            break
    
    # 查找HTTP方法
    method_patterns = [
        r'\b(POST|GET|PUT|DELETE)\b',
        r'"method":\s*"(POST|GET|PUT|DELETE)"'
    ]
    
    for pattern in method_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            endpoint_info["method"] = matches[0].upper()
            break
    
    return endpoint_info

async def main():
    """主函数"""
    print("🚀 开始获取API文档...")
    
    # 创建HTTP会话
    timeout = aiohttp.ClientTimeout(total=30)
    connector = aiohttp.TCPConnector(limit=10, limit_per_host=3)
    
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        # 并发获取所有API文档
        tasks = [fetch_api_doc(session, api_info) for api_info in API_DOCS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 整理结果
        api_endpoints = {}
        for i, result in enumerate(results):
            if isinstance(result, dict) and result:
                api_name = API_DOCS[i]['name']
                api_endpoints[api_name] = result
                print(f"📋 {api_name}: {result.get('method', 'POST')} {result.get('endpoint', 'unknown')}")
        
        # 保存结果到JSON文件
        output_file = "api_endpoints.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(api_endpoints, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ API端点信息已保存到 {output_file}")
        
        # 如果成功获取到端点信息，生成客户端更新代码
        if api_endpoints:
            generate_client_updates(api_endpoints)

def generate_client_updates(api_endpoints: Dict):
    """根据获取到的API端点信息生成客户端更新代码"""
    print("\n🔧 正在生成客户端更新代码...")
    
    updates = []
    
    for api_name, info in api_endpoints.items():
        endpoint = info.get('endpoint', '')
        method = info.get('method', 'POST')
        
        if endpoint:
            # 根据API名称映射到对应的方法名
            method_name = api_name_to_method_name(api_name)
            
            update_code = f"""
    async def {method_name}(self, data: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"\"\"\"
        return await self._make_request("{method}", "{endpoint}", data)
"""
            updates.append((api_name, method_name, endpoint, update_code))
    
    # 保存更新代码到文件
    with open("client_updates.py", 'w', encoding='utf-8') as f:
        f.write("# 客户端更新代码\n")
        f.write("# 根据API文档自动生成\n\n")
        
        for api_name, method_name, endpoint, code in updates:
            f.write(f"# {api_name} - {endpoint}\n")
            f.write(code)
            f.write("\n")
    
    print("✅ 客户端更新代码已保存到 client_updates.py")

def api_name_to_method_name(api_name: str) -> str:
    """将API名称转换为方法名"""
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