#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Veo3视频生成异步测试脚本

演示正确的异步使用方式：
1. 创建任务，立即获取task_id
2. 轮询任务状态，直到完成
3. 获取生成的视频URL
"""

import asyncio
import json
import time
from typing import Optional, Dict, Any
import aiohttp

BASE_URL = "http://localhost:5512"

async def create_veo3_task(prompt: str, model: str = "veo3") -> Optional[str]:
    """
    创建Veo3视频生成任务
    
    Returns:
        task_id: 任务ID，用于后续查询状态
    """
    async with aiohttp.ClientSession() as session:
        try:
            data = {
                "prompt": prompt,
                "model": model,
                "enhance_prompt": True
            }
            
            print(f"🚀 Creating Veo3 video task...")
            print(f"📝 Prompt: {prompt}")
            print(f"🤖 Model: {model}")
            
            async with session.post(
                f"{BASE_URL}/api/veo3/generate",
                json=data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        task_data = result.get("data", {})
                        task_id = task_data.get("id") or task_data.get("task_id")
                        print(f"✅ Task created successfully!")
                        print(f"🆔 Task ID: {task_id}")
                        return task_id
                    else:
                        print(f"❌ Task creation failed: {result.get('error', 'Unknown error')}")
                        return None
                else:
                    error_text = await response.text()
                    print(f"❌ HTTP Error {response.status}: {error_text}")
                    return None
                    
        except asyncio.TimeoutError:
            print("⏰ Task creation timed out (this might indicate the API is not working in async mode)")
            return None
        except Exception as e:
            print(f"❌ Error creating task: {e}")
            return None

async def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """
    查询任务状态
    
    Returns:
        任务状态信息
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{BASE_URL}/api/veo3/task",
                params={"id": task_id},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        return result.get("data")
                    else:
                        print(f"❌ Query failed: {result.get('error', 'Unknown error')}")
                        return None
                else:
                    error_text = await response.text()
                    print(f"❌ HTTP Error {response.status}: {error_text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error querying task: {e}")
            return None

async def poll_task_completion(task_id: str, max_wait_time: int = 300, poll_interval: int = 10) -> Optional[Dict[str, Any]]:
    """
    轮询任务直到完成
    
    Args:
        task_id: 任务ID
        max_wait_time: 最大等待时间（秒）
        poll_interval: 轮询间隔（秒）
    
    Returns:
        完成的任务结果
    """
    print(f"\n🔄 Starting to poll task status...")
    print(f"⏰ Max wait time: {max_wait_time}s, Poll interval: {poll_interval}s")
    
    start_time = time.time()
    attempt = 1
    
    while time.time() - start_time < max_wait_time:
        print(f"\n📊 Polling attempt #{attempt} (after {int(time.time() - start_time)}s)")
        
        task_data = await get_task_status(task_id)
        if task_data:
            status = task_data.get("status", "unknown")
            print(f"📈 Status: {status}")
            
            # 根据不同状态处理
            if status in ["completed", "success", "finished"]:
                print(f"🎉 Task completed successfully!")
                video_url = task_data.get("video_url") or task_data.get("result", {}).get("video_url")
                if video_url:
                    print(f"🎬 Video URL: {video_url}")
                return task_data
                
            elif status in ["failed", "error"]:
                print(f"💥 Task failed!")
                error_msg = task_data.get("error") or task_data.get("message", "Unknown error")
                print(f"❌ Error: {error_msg}")
                return task_data
                
            elif status in ["processing", "running", "pending", "queued"]:
                progress = task_data.get("progress", "Unknown")
                print(f"⏳ Still processing... Progress: {progress}")
                
            else:
                print(f"❓ Unknown status: {status}")
                print(f"📄 Full response: {json.dumps(task_data, indent=2, ensure_ascii=False)}")
        
        print(f"😴 Waiting {poll_interval}s before next poll...")
        await asyncio.sleep(poll_interval)
        attempt += 1
    
    print(f"\n⏰ Timeout reached after {max_wait_time}s")
    return None

async def test_veo3_async_workflow():
    """测试完整的异步工作流程"""
    print("=" * 60)
    print("🎬 Veo3 Video Generation Async Test")
    print("=" * 60)
    
    # 1. 创建任务
    prompt = "一只可爱的小猫在花园里玩耍，阳光明媚，温馨治愈"
    task_id = await create_veo3_task(prompt, "veo3")
    
    if not task_id:
        print("💥 Failed to create task, exiting...")
        return
    
    # 2. 轮询任务状态
    result = await poll_task_completion(task_id, max_wait_time=300, poll_interval=10)
    
    if result:
        print(f"\n🏁 Final result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"\n❌ Task did not complete within the timeout period")
        print(f"🔍 You can manually check the task status later using:")
        print(f"   curl '{BASE_URL}/api/veo3/task?id={task_id}'")

if __name__ == "__main__":
    # 运行异步测试
    asyncio.run(test_veo3_async_workflow())