#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Kling API MCP 服务主模块

使用 FastMCP 框架实现 Kling API 的 MCP 协议支持
"""

from fastmcp import FastMCP
import logging

from .kling_tools import (
    create_text_to_image_tool,
    create_text_to_video_tool,
    create_image_to_video_tool,
    create_virtual_try_on_tool,
    get_task_status_tool,
    get_task_result_tool,
    get_single_task_tool,
    wait_for_task_completion_tool
)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建MCP应用 - 优化配置以提高连接稳定性
mcp = FastMCP(
    "Kling API",
    # 启用短期缓存以提高连接稳定性
    cache_expiration_seconds=30.0,
    # 简化错误处理
    mask_error_details=False,
    # 处理重复工具时的行为
    on_duplicate_tools="ignore",
    on_duplicate_resources="ignore", 
    on_duplicate_prompts="ignore",
    # 添加连接管理配置
    max_message_size=1024*1024,  # 1MB消息大小限制
    keep_alive_interval=10.0,    # 10秒心跳间隔
    connection_timeout=60.0       # 60秒连接超时
)

# 注册所有工具模块
logger.info("开始注册Kling API MCP工具模块...")
mcp.add_tool(create_text_to_image_tool)
mcp.add_tool(create_text_to_video_tool) 
mcp.add_tool(create_image_to_video_tool)
mcp.add_tool(create_virtual_try_on_tool)
mcp.add_tool(get_task_status_tool)
mcp.add_tool(get_task_result_tool)
mcp.add_tool(get_single_task_tool)
mcp.add_tool(wait_for_task_completion_tool)

logger.info("✅ Kling API MCP工具模块注册完成")

@mcp.resource("kling://config")
def get_mcp_config():
    """MCP配置信息"""
    return {
        "name": "Kling API",
        "version": "1.0.0",
        "description": "Kling AI生成API的MCP工具集合",
        "modules": [
            "text_to_image", "text_to_video", "image_to_video", 
            "virtual_try_on", "task_management"
        ],
        "cache_config": {
            "expiration_seconds": 30.0,
            "sync_mode": True
        },
        "api_key_managed": True,
        "features": [
            "文生图", "文生视频", "图生视频", "虚拟换衣", "任务管理"
        ]
    }

@mcp.prompt("kling_usage_guide")
def kling_usage_guide():
    """Kling API使用指南"""
    return """
# Kling AI生成API使用指南

## 功能概览
Kling API提供多种AI生成功能：

### 1. 文生图 (Text-to-Image)
根据文本描述生成高质量图像
- **工具**: create_text_to_image_tool
- **参数**: prompt（必需）, aspect_ratio, cfg_scale, seed
- **格式**: 支持1:1, 16:9, 9:16, 4:3, 3:4等宽高比

### 2. 文生视频 (Text-to-Video) 
根据文本描述生成视频内容
- **工具**: create_text_to_video_tool
- **参数**: prompt（必需）, aspect_ratio, duration, cfg_scale, seed
- **时长**: 支持5秒、10秒视频生成

### 3. 图生视频 (Image-to-Video)
基于输入图像生成相关视频
- **工具**: create_image_to_video_tool
- **参数**: image_url（必需）, prompt, duration, cfg_scale, seed
- **说明**: 图片URL必须是有效的HTTP/HTTPS链接

### 4. 虚拟换衣 (Virtual Try-On)
AI驱动的虚拟试衣功能
- **工具**: create_virtual_try_on_tool
- **参数**: person_image（必需）, garment_image（必需）, category
- **类别**: tops(上装), bottoms(下装), dresses(连衣裙), outerwear(外套)

### 5. 任务管理
- **get_task_status_tool**: 查询任务状态和进度
- **get_task_result_tool**: 获取完成任务的结果
- **get_single_task_tool**: 获取任务完整信息
- **wait_for_task_completion_tool**: 等待任务完成

## 重要提示
- ✅ API-KEY已在服务端配置，无需手动传递
- 🎯 所有任务都是异步处理，创建后需要查询状态
- 📊 任务状态包括: submitted, processing, completed, failed
- 🔄 建议使用轮询方式检查任务进度
- 📝 保存task_id用于后续查询和获取结果

## 最佳实践
1. **文本提示词**: 详细描述想要的结果，包含风格、情感、环境等信息
2. **参数调优**: 根据需求调整cfg_scale控制生成强度
3. **任务监控**: 及时查询任务状态，避免重复提交
4. **错误处理**: 检查返回的错误信息，调整参数重试
"""

# 导出app变量供外部使用 - 关键！
app = mcp