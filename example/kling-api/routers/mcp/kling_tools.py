#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Kling API MCP 工具函数

为 MCP 协议提供 Kling API 功能封装
"""

from typing import Dict, List, Optional, Any, Union
import json

from services.kling_service import get_kling_service
from core.kling_client import KlingAPIError
from core.logger import get_mcp_logger, log_exception
from core.config import settings

logger = get_mcp_logger()

# =============================================================================
# MCP 工具函数实现
# =============================================================================

async def create_text_to_image_tool(
    prompt: str,
    aspect_ratio: str = "1:1",
    negative_prompt: Optional[str] = None,
    cfg_scale: float = 7.5,
    seed: Optional[int] = None
) -> str:
    """
    创建文生图任务
    
    Args:
        prompt: 文本描述，详细描述想要生成的图像内容
        aspect_ratio: 宽高比，支持: 1:1, 16:9, 9:16, 4:3, 3:4，默认 1:1
        negative_prompt: 负面提示词，描述不想要的内容（可选）
        cfg_scale: CFG缩放值，控制生成与提示词的匹配程度，范围1.0-20.0，默认7.5
        seed: 随机种子，用于复现结果（可选）
    
    Returns:
        JSON格式的任务创建结果，包含任务ID和其他信息
    """
    try:
        service = get_kling_service()
        
        result = await service.create_text_to_image_task(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            negative_prompt=negative_prompt,
            cfg_scale=cfg_scale,
            seed=seed
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to create text-to-image task")
        error_result = {
            "error": True,
            "message": str(e),
            "type": type(e).__name__
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

async def create_text_to_video_tool(
    prompt: str,
    aspect_ratio: str = "16:9",
    duration: int = 5,
    cfg_scale: float = 7.5,
    seed: Optional[int] = None
) -> str:
    """
    创建文生视频任务
    
    Args:
        prompt: 文本描述，详细描述想要生成的视频内容
        aspect_ratio: 宽高比，支持: 16:9, 9:16, 1:1，默认 16:9
        duration: 视频时长（秒），支持: 5, 10，默认 5
        cfg_scale: CFG缩放值，范围1.0-20.0，默认7.5
        seed: 随机种子（可选）
    
    Returns:
        JSON格式的任务创建结果
    """
    try:
        service = get_kling_service()
        
        result = await service.create_text_to_video_task(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            duration=duration,
            cfg_scale=cfg_scale,
            seed=seed
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to create text-to-video task")
        error_result = {
            "error": True,
            "message": str(e),
            "type": type(e).__name__
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

async def create_image_to_video_tool(
    image_url: str,
    prompt: Optional[str] = None,
    duration: int = 5,
    cfg_scale: float = 7.5,
    seed: Optional[int] = None
) -> str:
    """
    创建图生视频任务
    
    Args:
        image_url: 输入图片的URL地址，必须是有效的HTTP/HTTPS链接
        prompt: 可选的文本描述，用于指导视频生成
        duration: 视频时长（秒），支持: 5, 10，默认 5
        cfg_scale: CFG缩放值，范围1.0-20.0，默认7.5
        seed: 随机种子（可选）
    
    Returns:
        JSON格式的任务创建结果
    """
    try:
        service = get_kling_service()
        
        result = await service.create_image_to_video_task(
            image_url=image_url,
            prompt=prompt,
            duration=duration,
            cfg_scale=cfg_scale,
            seed=seed
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to create image-to-video task")
        error_result = {
            "error": True,
            "message": str(e),
            "type": type(e).__name__
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

async def create_virtual_try_on_tool(
    person_image: str,
    garment_image: str,
    category: str = "tops"
) -> str:
    """
    创建虚拟换衣任务
    
    Args:
        person_image: 人物图片URL，必须是有效的HTTP/HTTPS链接
        garment_image: 服装图片URL，必须是有效的HTTP/HTTPS链接
        category: 服装类别，支持: tops(上装), bottoms(下装), dresses(连衣裙), outerwear(外套)，默认 tops
    
    Returns:
        JSON格式的任务创建结果
    """
    try:
        service = get_kling_service()
        
        result = await service.create_virtual_try_on_task(
            person_image=person_image,
            garment_image=garment_image,
            category=category
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to create virtual try-on task")
        error_result = {
            "error": True,
            "message": str(e),
            "type": type(e).__name__
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

async def get_task_status_tool(
    task_id: str
) -> str:
    """
    获取任务状态
    
    Args:
        task_id: 任务ID，从创建任务接口返回的结果中获取
    
    Returns:
        JSON格式的任务状态信息，包含状态、进度等
    """
    try:
        service = get_kling_service()
        
        result = await service.get_task_status(
            task_id=task_id
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, f"Failed to get task status for {task_id}")
        error_result = {
            "error": True,
            "message": str(e),
            "type": type(e).__name__,
            "task_id": task_id
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

async def get_task_result_tool(
    task_id: str
) -> str:
    """
    获取任务结果
    
    Args:
        task_id: 任务ID，从创建任务接口返回的结果中获取
    
    Returns:
        JSON格式的任务结果，包含生成文件的下载链接等
    """
    try:
        service = get_kling_service()
        
        result = await service.get_task_result(
            task_id=task_id
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, f"Failed to get task result for {task_id}")
        error_result = {
            "error": True,
            "message": str(e),
            "type": type(e).__name__,
            "task_id": task_id
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

async def get_single_task_tool(
    task_id: str
) -> str:
    """
    获取单个任务的完整信息
    
    Args:
        task_id: 任务ID，从创建任务接口返回的结果中获取
    
    Returns:
        JSON格式的任务完整信息，包括状态、进度、结果、错误信息等所有详情
    """
    try:
        service = get_kling_service()
        
        result = await service.get_single_task(
            task_id=task_id
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, f"Failed to get task info for {task_id}")
        error_result = {
            "error": True,
            "message": str(e),
            "type": type(e).__name__,
            "task_id": task_id
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

async def wait_for_task_completion_tool(
    task_id: str,
    timeout: int = 300,
    poll_interval: int = 5
) -> str:
    """
    等待任务完成并返回最终结果
    
    Args:
        task_id: 任务ID，从创建任务接口返回的结果中获取
        timeout: 超时时间（秒），最大600秒，默认300秒
        poll_interval: 轮询间隔（秒），最小1秒，默认5秒
    
    Returns:
        JSON格式的最终任务结果，如果任务成功完成则包含结果文件链接，如果失败则包含错误信息
    """
    try:
        # 参数验证
        if timeout > 600:
            raise ValueError("Timeout cannot exceed 600 seconds")
        if poll_interval < 1:
            raise ValueError("Poll interval must be at least 1 second")
        
        service = get_kling_service()
        
        result = await service.wait_for_task_completion(
            task_id=task_id,
            timeout=timeout,
            poll_interval=poll_interval
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except TimeoutError as e:
        timeout_result = {
            "error": True,
            "message": f"Task wait timeout: {str(e)}",
            "type": "TimeoutError",
            "task_id": task_id,
            "timeout_seconds": timeout
        }
        return json.dumps(timeout_result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, f"Failed to wait for task completion: {task_id}")
        error_result = {
            "error": True,
            "message": str(e),
            "type": type(e).__name__,
            "task_id": task_id
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

# =============================================================================
# 工具函数元信息
# =============================================================================

# 为每个工具函数添加描述信息
create_text_to_image_tool.__doc__ = """创建文生图任务 - 根据文本描述生成图像"""
create_text_to_video_tool.__doc__ = """创建文生视频任务 - 根据文本描述生成视频"""
create_image_to_video_tool.__doc__ = """创建图生视频任务 - 根据输入图像生成视频"""
create_virtual_try_on_tool.__doc__ = """创建虚拟换衣任务 - 对人物图像进行虚拟换衣"""
get_task_status_tool.__doc__ = """获取任务状态 - 查询任务当前状态和进度"""
get_task_result_tool.__doc__ = """获取任务结果 - 获取已完成任务的结果文件"""
get_single_task_tool.__doc__ = """获取任务完整信息 - 获取任务的所有详细信息"""
wait_for_task_completion_tool.__doc__ = """等待任务完成 - 阻塞等待任务完成并返回结果"""