#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Images API 测试脚本

测试各种图像生成API的功能
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import settings

async def test_gpt_image():
    """测试GPT图像生成"""
    url = f"http://{settings.server.host}:{settings.server.port}{settings.api_prefix}/gpt/generations"
    
    data = {
        "prompt": "A beautiful sunset over a mountain landscape",
        "model": "dall-e-3",
        "size": "1024x1024",
        "quality": "standard",
        "style": "vivid"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=data) as response:
                result = await response.json()
                print(f"GPT Image Generation Test - Status: {response.status}")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return response.status == 200
        except Exception as e:
            print(f"GPT Image Generation Test Failed: {e}")
            return False

async def test_recraft_image():
    """测试Recraft图像生成"""
    url = f"http://{settings.server.host}:{settings.server.port}{settings.api_prefix}/recraft/generate"
    
    data = {
        "prompt": "A futuristic city with flying cars",
        "style": "realistic",
        "size": "1024x1024",
        "image_format": "png"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=data) as response:
                result = await response.json()
                print(f"Recraft Image Generation Test - Status: {response.status}")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return response.status == 200
        except Exception as e:
            print(f"Recraft Image Generation Test Failed: {e}")
            return False

async def test_seedream_image():
    """测试即梦3.0图像生成"""
    url = f"http://{settings.server.host}:{settings.server.port}{settings.api_prefix}/seedream/generate"
    
    data = {
        "prompt": "一只可爱的熊猫在竹林中玩耍",
        "aspect_ratio": "1:1",
        "cfg_scale": 7.5,
        "seed": 12345
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=data) as response:
                result = await response.json()
                print(f"Seedream Image Generation Test - Status: {response.status}")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return response.status == 200
        except Exception as e:
            print(f"Seedream Image Generation Test Failed: {e}")
            return False

async def test_health_check():
    """测试健康检查"""
    url = f"http://{settings.server.host}:{settings.server.port}{settings.api_prefix}/health"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                result = await response.json()
                print(f"Health Check Test - Status: {response.status}")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return response.status == 200
        except Exception as e:
            print(f"Health Check Test Failed: {e}")
            return False

async def test_stable_diffusion_image():
    """测试StableDiffusion图像生成"""
    url = f"http://{settings.server.host}:{settings.server.port}{settings.api_prefix}/stable-diffusion/create"
    
    data = {
        "prompt": "A cyberpunk cityscape at night",
        "negative_prompt": "blurry, low quality",
        "width": 1024,
        "height": 1024,
        "steps": 20,
        "guidance_scale": 7.5
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=data) as response:
                result = await response.json()
                print(f"StableDiffusion Image Generation Test - Status: {response.status}")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return response.status == 200
        except Exception as e:
            print(f"StableDiffusion Image Generation Test Failed: {e}")
            return False

async def test_virtual_try_on():
    """测试虚拟换衣"""
    url = f"http://{settings.server.host}:{settings.server.port}{settings.api_prefix}/virtual-try-on/generate"
    
    data = {
        "person_image": "https://example.com/person.jpg",
        "garment_image": "https://example.com/garment.jpg",
        "category": "tops"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=data) as response:
                result = await response.json()
                print(f"Virtual Try-on Test - Status: {response.status}")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return response.status == 200
        except Exception as e:
            print(f"Virtual Try-on Test Failed: {e}")
            return False

async def test_hailuo_image():
    """测试海螺图片生成"""
    url = f"http://{settings.server.host}:{settings.server.port}{settings.api_prefix}/hailuo/generate"
    
    data = {
        "prompt": "一只在月光下的狼",
        "size": "1024x1024",
        "quality": "standard"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=data) as response:
                result = await response.json()
                print(f"Hailuo Image Generation Test - Status: {response.status}")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return response.status == 200
        except Exception as e:
            print(f"Hailuo Image Generation Test Failed: {e}")
            return False

async def test_doubao_image():
    """测试Doubao图片生成"""
    url = f"http://{settings.server.host}:{settings.server.port}{settings.api_prefix}/doubao/generate"
    
    data = {
        "prompt": "一个科幻机器人在未来城市中行走",
        "size": "1024x1024",
        "quality": "standard",
        "num_images": 1
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=data) as response:
                result = await response.json()
                print(f"Doubao Image Generation Test - Status: {response.status}")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return response.status == 200
        except Exception as e:
            print(f"Doubao Image Generation Test Failed: {e}")
            return False

async def main():
    """运行所有测试"""
    print("Starting Images API Tests...")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("GPT Image Generation", test_gpt_image),
        ("Recraft Image Generation", test_recraft_image),
        ("Seedream Image Generation", test_seedream_image),
        ("StableDiffusion Image Generation", test_stable_diffusion_image),
        ("Virtual Try-on", test_virtual_try_on),
        ("Hailuo Image Generation", test_hailuo_image),
        ("Doubao Image Generation", test_doubao_image),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        try:
            success = await test_func()
            results.append((test_name, success))
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{status}\n")
        except Exception as e:
            print(f"❌ FAILED: {e}\n")
            results.append((test_name, False))
    
    # 总结
    print("=" * 50)
    print("Test Results Summary:")
    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())