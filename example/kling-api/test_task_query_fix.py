#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试Kling API任务查询修复
"""

import asyncio
import json
from core.kling_client import KlingAPIClient, KlingAPIError

async def test_task_query_endpoints():
    """测试任务查询端点路径构建"""
    client = KlingAPIClient()
    
    # 测试端点模板
    task_id = "test-task-123"
    expected_endpoints = {
        "text_to_image": f"/kling/v1/images/generations/{task_id}",
        "text_to_video": f"/kling/v1/videos/text2video/{task_id}",
        "image_to_video": f"/kling/v1/videos/image2video/{task_id}",
        "virtual_try_on": f"/kling/v1/images/kolors-virtual-try-on/{task_id}"
    }
    
    print("=== 测试端点路径构建 ===")
    for task_type, expected_endpoint in expected_endpoints.items():
        template = client.endpoints["task_query_templates"][task_type]
        actual_endpoint = template.format(task_id=task_id)
        
        print(f"任务类型: {task_type}")
        print(f"期望端点: {expected_endpoint}")
        print(f"实际端点: {actual_endpoint}")
        print(f"匹配结果: {'✓' if actual_endpoint == expected_endpoint else '✗'}")
        print("-" * 50)
    
    print("\n=== 测试请求头设置 ===")
    # 检查默认请求头是否包含模拟浏览器信息
    session = await client._get_session()
    print("会话默认头部:", dict(session.headers))
    
    await client.close()

def test_api_documentation_compliance():
    """测试API文档兼容性"""
    print("\n=== API文档兼容性检查 ===")
    
    # 根据API文档验证路径格式
    doc_format = "/YOUR_BASE_URL/kling/v1/{action}/{action2}/{task_id}"
    
    mappings = {
        "text_to_image": ("images", "generations"),
        "text_to_video": ("videos", "text2video"), 
        "image_to_video": ("videos", "image2video"),
        "virtual_try_on": ("images", "kolors-virtual-try-on")
    }
    
    task_id = "example-task-456"
    
    for task_type, (action, action2) in mappings.items():
        expected = f"/kling/v1/{action}/{action2}/{task_id}"
        print(f"{task_type}: {expected}")
    
    print("\n=== 响应格式检查 ===")
    expected_response_fields = [
        "code", "message", "request_id", "data"
    ]
    expected_data_fields = [
        "task_id", "task_status", "created_at", "updated_at", 
        "task_info", "task_result"
    ]
    
    print("期望响应字段:", expected_response_fields)
    print("期望数据字段:", expected_data_fields)

if __name__ == "__main__":
    print("开始测试Kling API任务查询修复...")
    
    # 测试端点构建
    asyncio.run(test_task_query_endpoints())
    
    # 测试文档兼容性
    test_api_documentation_compliance()
    
    print("\n测试完成！")