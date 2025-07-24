#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Kling API 测试脚本

测试 FastAPI 和 MCP 服务是否正常工作
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 测试配置
FASTAPI_BASE_URL = "http://localhost:5511"
MCP_BASE_URL = "http://localhost:5510"
TEST_API_KEY = "sk-idDBqyoDVqCXInnO9uaGLUfwsxY7RhzHSn166z5jOBCBvFmY"

async def test_fastapi_health():
    """测试 FastAPI 健康检查"""
    print("🔍 Testing FastAPI health check...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{FASTAPI_BASE_URL}/health") as response:
                if response.status == 200:
                    print("✅ FastAPI health check passed")
                    return True
                else:
                    print(f"❌ FastAPI health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ FastAPI health check error: {e}")
            return False

async def test_fastapi_root():
    """测试 FastAPI 根路径"""
    print("🔍 Testing FastAPI root endpoint...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{FASTAPI_BASE_URL}/") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ FastAPI root endpoint accessible")
                    print(f"   Service: {data.get('service', 'N/A')}")
                    print(f"   Version: {data.get('version', 'N/A')}")
                    return True
                else:
                    print(f"❌ FastAPI root endpoint failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ FastAPI root endpoint error: {e}")
            return False

async def test_fastapi_text_to_image():
    """测试 FastAPI 文生图接口"""
    print("🔍 Testing FastAPI text-to-image endpoint...")
    
    headers = {
        "Authorization": f"Bearer {TEST_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "prompt": "一只可爱的小猫",
        "aspect_ratio": "1:1",
        "cfg_scale": 7.5
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{FASTAPI_BASE_URL}/api/images/generations",
                headers=headers,
                json=data
            ) as response:
                response_text = await response.text()
                print(f"   Status: {response.status}")
                print(f"   Response: {response_text[:200]}...")
                
                if response.status in [200, 400, 401]:  # 200=成功, 400/401=预期的认证/参数错误
                    print("✅ FastAPI text-to-image endpoint accessible")
                    return True
                else:
                    print(f"❌ FastAPI text-to-image unexpected status: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ FastAPI text-to-image error: {e}")
            return False

async def test_mcp_health():
    """测试 MCP 服务健康状态"""
    print("🔍 Testing MCP service connectivity...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # MCP 协议的基本连通性测试
            async with session.post(
                f"{MCP_BASE_URL}/mcp/v1",
                headers={"Content-Type": "application/json"},
                json={"jsonrpc": "2.0", "method": "tools/list", "id": "test"}
            ) as response:
                print(f"   MCP Status: {response.status}")
                response_text = await response.text()
                print(f"   MCP Response: {response_text[:200]}...")
                
                if response.status in [200, 400, 404]:  # 某种响应表示服务在运行
                    print("✅ MCP service is accessible")
                    return True
                else:
                    print(f"❌ MCP service unexpected status: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ MCP service connectivity error: {e}")
            return False

async def run_tests():
    """运行所有测试"""
    print("🚀 Starting Kling API Service Tests\n")
    
    tests = [
        ("FastAPI Health Check", test_fastapi_health),
        ("FastAPI Root Endpoint", test_fastapi_root),
        ("FastAPI Text-to-Image", test_fastapi_text_to_image),
        ("MCP Service Connectivity", test_mcp_health),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # 输出测试总结
    print(f"\n{'='*50}")
    print("🏁 Test Results Summary")
    print('='*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Tests: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Services are working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the service status.")
        return False

def main():
    """主函数"""
    try:
        success = asyncio.run(run_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test runner error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()