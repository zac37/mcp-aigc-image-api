#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
深度分析API文档，提取真实的端点信息
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

async def deep_analyze_api(session: aiohttp.ClientSession, url: str, name: str) -> Dict:
    """深度分析单个API文档"""
    try:
        print(f"🔍 深度分析 {name}...")
        
        async with session.get(url, headers=BROWSER_HEADERS) as response:
            if response.status == 200:
                html_content = await response.text()
                
                # 保存原始HTML用于调试
                with open(f"debug_{name.replace(' ', '_')}.html", 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                # 解析HTML
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # 提取所有文本内容
                text_content = soup.get_text()
                
                # 多重解析策略
                api_info = {
                    "name": name,
                    "url": url,
                    "endpoint": "",
                    "method": "POST",
                    "model_name": "",
                    "request_format": {},
                    "raw_paths": [],
                    "all_urls": []
                }
                
                # 策略1: 查找所有可能的URL路径
                url_patterns = [
                    r'https://api\.chatfire\.cn(/[^\s\'"<>]*)',
                    r'POST\s+(/[^\s\'"<>]+)',
                    r'GET\s+(/[^\s\'"<>]+)',
                    r'"path":\s*"([^"]+)"',
                    r"'path':\s*'([^']+)'",
                    r'/v1/[^\s\'"<>]+',
                    r'/[a-zA-Z]+/[a-zA-Z0-9\-]+',
                ]
                
                for pattern in url_patterns:
                    matches = re.findall(pattern, text_content, re.IGNORECASE)
                    for match in matches:
                        if len(match) > 1 and match.startswith('/'):
                            api_info["raw_paths"].append(match)
                
                # 策略2: 查找完整URL
                full_url_pattern = r'https://api\.chatfire\.cn[^\s\'"<>]*'
                full_urls = re.findall(full_url_pattern, text_content, re.IGNORECASE)
                api_info["all_urls"] = list(set(full_urls))
                
                # 策略3: 查找模型名称
                model_patterns = [
                    r'"model":\s*"([^"]+)"',
                    r"'model':\s*'([^']+)'",
                    r'模型[：:]?\s*([a-zA-Z0-9\-]+)',
                    r'dall-e[0-9\-]*',
                    r'recraft[a-zA-Z0-9\-]*',
                    r'seedream[a-zA-Z0-9\-]*',
                    r'stable[a-zA-Z0-9\-]*',
                    r'flux[a-zA-Z0-9\-]*',
                    r'hailuo[a-zA-Z0-9\-]*',
                    r'doubao[a-zA-Z0-9\-]*',
                ]
                
                for pattern in model_patterns:
                    matches = re.findall(pattern, text_content, re.IGNORECASE)
                    if matches:
                        api_info["model_name"] = matches[0]
                        break
                
                # 策略4: 查找JSON请求示例
                json_patterns = [
                    r'\{[^{}]*"prompt"[^{}]*\}',
                    r'\{[^{}]*"text"[^{}]*\}',
                    r'\{[^{}]*"model"[^{}]*\}',
                ]
                
                for pattern in json_patterns:
                    matches = re.findall(pattern, text_content, re.DOTALL)
                    for match in matches:
                        try:
                            # 尝试解析JSON
                            json_obj = json.loads(match)
                            if len(json_obj) > 0:
                                api_info["request_format"] = json_obj
                                break
                        except:
                            continue
                    if api_info["request_format"]:
                        break
                
                # 策略5: 根据API名称和内容推断端点
                api_info["endpoint"] = infer_endpoint(name, api_info)
                
                print(f"✅ {name}: {api_info['endpoint']} (模型: {api_info.get('model_name', 'unknown')})")
                
                return api_info
                
            else:
                print(f"❌ 获取 {name} 失败: HTTP {response.status}")
                return None
                
    except Exception as e:
        print(f"❌ 分析 {name} 出错: {str(e)}")
        return None

def infer_endpoint(api_name: str, api_info: Dict) -> str:
    """根据API名称和解析内容推断正确的端点"""
    
    # 首先查看是否有解析到的路径
    raw_paths = api_info.get("raw_paths", [])
    if raw_paths:
        # 优先选择包含模型名的路径
        for path in raw_paths:
            if any(keyword in path.lower() for keyword in ["recraft", "seedream", "flux", "stable", "hailuo", "doubao", "virtual"]):
                return path
        
        # 选择最有可能的路径（不是太通用的）
        for path in raw_paths:
            if len(path) > 5 and not path.endswith('/'):
                return path
    
    # 根据API名称推断
    name_lower = api_name.lower()
    
    if "recraft" in name_lower:
        return "/v1/images/generations"  # Recraft可能也用通用端点，但需要指定model参数
    elif "seedream" in name_lower or "即梦" in name_lower:
        return "/v1/images/generations"  # 同上
    elif "stable" in name_lower:
        return "/v1/images/generations"  # 同上
    elif "虚拟换衣" in name_lower or "virtual" in name_lower:
        return "/v1/images/virtual-try-on"  # 可能的虚拟换衣端点
    elif "hailuo" in name_lower or "海螺" in name_lower:
        return "/v1/images/generations"  # 同上
    elif "doubao" in name_lower:
        return "/v1/images/generations"  # 同上
    elif "gpt" in name_lower:
        return "/v1/images/generations"  # GPT已确认正确
    else:
        return "/v1/images/generations"  # 默认端点

async def main():
    """主函数"""
    print("🚀 开始深度分析API文档...")
    
    # 重点API文档
    priority_apis = [
        ("Recraft图像生成", "https://apifox.com/apidoc/docs-site/3916055/263578635e0.md"),
        ("虚拟换衣", "https://apifox.com/apidoc/docs-site/3916055/226983436e0.md"),
        ("Seedream图像生成", "https://apifox.com/apidoc/docs-site/3916055/285414862e0.md"),
        ("海螺图片", "https://apifox.com/apidoc/docs-site/3916055/295927715e0.md"),
    ]
    
    # 创建HTTP会话
    timeout = aiohttp.ClientTimeout(total=30)
    connector = aiohttp.TCPConnector(limit=10, limit_per_host=3)
    
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        results = {}
        
        for name, url in priority_apis:
            result = await deep_analyze_api(session, url, name)
            if result:
                results[name] = result
            
            # 延迟避免请求过快
            await asyncio.sleep(2)
        
        # 保存详细分析结果
        with open("deep_analysis_results.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 深度分析结果已保存到 deep_analysis_results.json")
        
        # 生成端点配置
        generate_endpoint_config(results)

def generate_endpoint_config(results: Dict):
    """生成端点配置代码"""
    print("\n🔧 生成端点配置...")
    
    config_lines = []
    config_lines.append("# 根据深度分析生成的API端点配置")
    config_lines.append("# 每个模型使用正确的端点和参数")
    config_lines.append("")
    
    endpoint_mapping = {}
    
    for name, info in results.items():
        endpoint = info.get('endpoint', '/v1/images/generations')
        model_name = info.get('model_name', '')
        request_format = info.get('request_format', {})
        
        # 生成方法名
        method_name = name_to_method_name(name)
        
        config_lines.append(f"# {name}")
        config_lines.append(f"# 端点: {endpoint}")
        config_lines.append(f"# 模型: {model_name}")
        config_lines.append(f"# 请求格式: {json.dumps(request_format, ensure_ascii=False)}")
        
        endpoint_mapping[method_name] = {
            "endpoint": endpoint,
            "model": model_name,
            "request_format": request_format
        }
        
        config_lines.append("")
    
    # 保存配置
    with open("endpoint_config.py", 'w', encoding='utf-8') as f:
        f.write('\n'.join(config_lines))
        f.write(f"\n\n# 端点映射配置\nENDPOINT_MAPPING = {json.dumps(endpoint_mapping, ensure_ascii=False, indent=2)}")
    
    print("✅ 端点配置已保存到 endpoint_config.py")
    
    # 打印关键发现
    print("\n📋 关键发现:")
    for name, info in results.items():
        endpoint = info.get('endpoint', 'unknown')
        model = info.get('model_name', 'unknown')
        paths = info.get('raw_paths', [])
        print(f"  {name}:")
        print(f"    推荐端点: {endpoint}")
        print(f"    模型名称: {model}")
        if paths:
            print(f"    发现的路径: {paths[:3]}")  # 只显示前3个

def name_to_method_name(api_name: str) -> str:
    """将API名称转换为方法名"""
    mapping = {
        "Recraft图像生成": "recraft_generate",
        "Seedream图像生成": "seedream_generate",
        "虚拟换衣": "virtual_try_on_generate",
        "海螺图片": "hailuo_generate",
    }
    return mapping.get(api_name, "unknown_generate")

if __name__ == "__main__":
    asyncio.run(main())