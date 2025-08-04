#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Images API MCP 工具函数

为 MCP 协议提供 Images API 功能封装
"""

from typing import Dict, List, Optional, Any, Union
import json
import uuid

from services.images_service import get_images_service
from core.compatibility_adapter import ImagesAPIError
from core.logger import get_mcp_logger, log_exception
from core.simple_config import settings
from core.simple_task_queue import simple_task_queue, VideoTask

logger = get_mcp_logger()

# =============================================================================
# 异步存储辅助函数 (复用FastAPI逻辑)
# =============================================================================

def submit_image_storage_async(
    request_id: str,
    prompt: str,
    model: str,
    result_data: Any,
    generation_params: Optional[Dict[str, Any]] = None,
    enhanced_prompt: Optional[str] = None
):
    """
    异步提交图片存储任务（KISS原则：简单直接）
    复用FastAPI中的实现逻辑
    
    Args:
        request_id: API请求ID
        prompt: 生成提示词
        model: 使用的模型
        result_data: API返回的结果数据
        generation_params: 生成参数
        enhanced_prompt: 增强后的提示词
    """
    try:
        # 提取图片URLs
        image_urls = []
        
        # 处理不同的返回格式
        if isinstance(result_data, dict):
            # 格式1: {"data": [{"url": "..."}, ...]}
            if 'data' in result_data and isinstance(result_data['data'], list):
                for item in result_data['data']:
                    if isinstance(item, dict) and 'url' in item:
                        image_urls.append(item['url'])
            # 格式2: 直接是图片列表
            elif isinstance(result_data, list):
                for item in result_data:
                    if isinstance(item, dict) and 'url' in item:
                        image_urls.append(item['url'])
        elif isinstance(result_data, list):
            # 格式3: 直接是图片列表
            for item in result_data:
                if isinstance(item, dict) and 'url' in item:
                    image_urls.append(item['url'])
        
        if image_urls:
            # 动态导入避免循环依赖
            from celery_tasks import submit_image_storage_task
            
            # 如果没有直接传递enhanced_prompt，尝试从result_data中提取
            if not enhanced_prompt and isinstance(result_data, dict):
                enhanced_prompt = result_data.get('enhanced_prompt') or result_data.get('enhancedPrompt')
                if not enhanced_prompt and 'data' in result_data:
                    # 某些API可能在data字段中包含enhanced_prompt
                    if isinstance(result_data['data'], dict):
                        enhanced_prompt = result_data['data'].get('enhanced_prompt') or result_data['data'].get('enhancedPrompt')
            
            celery_task_id = submit_image_storage_task(
                request_id=request_id,
                prompt=prompt,
                model=model,
                image_urls=image_urls,
                generation_params=generation_params,
                enhanced_prompt=enhanced_prompt
            )
            
            logger.info(f"[{request_id}] MCP异步图片存储任务已提交: {celery_task_id}")
            return celery_task_id
        else:
            logger.warning(f"[{request_id}] 未找到可存储的图片URL")
            return None
            
    except Exception as e:
        logger.error(f"[{request_id}] 异步存储任务提交失败: {e}")
        # 不抛出异常，只记录错误，保证主流程正常
        return None

# =============================================================================
# MCP 工具函数实现
# =============================================================================

async def create_gpt_image_tool(
    prompt: str,
    model: str = "gpt-image-1",
    n: int = 1,
    response_format: str = "url",
    size: str = "auto",
    background: str = "auto",
    quality: str = "auto",
    moderation: str = "auto"
) -> str:
    """
    创建GPT图像生成任务
    
    Args:
        prompt: 图像描述提示词，详细描述想要生成的图像内容
        model: 模型名称，默认 gpt-image-1
        n: 生成图像数量，默认 1
        response_format: 返回格式 (url, b64_json, oss_url)，默认 url
        size: 图像尺寸 (1024x1024, 1536x1024, 1024x1536, auto)，默认 auto
        background: 背景类型 (transparent, opaque, auto)，默认 auto
        quality: 图像质量 (high, medium, low, auto)，默认 auto
        moderation: 内容审核级别 (low, auto)，默认 auto
    
    Returns:
        JSON格式的图像生成结果，包含图像URL和相关信息
    """
    request_id = str(uuid.uuid4())
    
    try:
        service = get_images_service()
        
        result = await service.create_gpt_image(
            prompt=prompt,
            model=model,
            n=n,
            response_format=response_format,
            size=size,
            background=background,
            quality=quality,
            moderation=moderation
        )
        
        # 异步提交图片存储任务（复用FastAPI逻辑）
        submit_image_storage_async(
            request_id=request_id,
            prompt=prompt,
            model=model,
            result_data=result,
            generation_params={
                "n": n,
                "response_format": response_format,
                "size": size,
                "background": background,
                "quality": quality,
                "moderation": moderation
            }
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to create GPT image")
        error_result = {
            "error": True,
            "message": str(e),
            "type": type(e).__name__
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

async def create_gpt_image_edit_tool(
    image_description: str = "请描述您要编辑的图片",
    prompt: str = "请描述您想要的编辑效果",
    model: str = "gpt-image-1",
    n: int = 1,
    size: str = "1024x1024",
    response_format: str = "url"
) -> str:
    """
    GPT图像编辑工具（虚拟接口）
    
    由于MCP协议不支持文件上传，此工具提供REST API调用指南
    
    Args:
        image_description: 要编辑的图片描述（仅用于说明）
        prompt: 编辑效果描述
        model: 模型名称，默认gpt-image-1
        n: 生成图片数量，1-10之间
        size: 图片尺寸，256x256/512x512/1024x1024
        response_format: 返回格式，url或b64_json
    
    Returns:
        REST API调用指南和curl示例
    """
    
    # 构建API调用说明
    api_guide = {
        "message": "MCP协议不支持文件上传，请使用以下REST API进行GPT图像编辑",
        "api_info": {
            "endpoint": "POST /api/gpt/edits",
            "base_url": "http://localhost:5512",
            "full_url": "http://localhost:5512/api/gpt/edits",
            "content_type": "multipart/form-data",
            "description": "GPT图像编辑接口 - 在给定原始图像和提示的情况下创建编辑或扩展图像"
        },
        "required_parameters": {
            "image": {
                "type": "file (binary)",
                "description": "要编辑的图像文件，必须是有效的PNG文件，小于4MB，方形"
            },
            "prompt": {
                "type": "string",
                "description": "所需图像的文本描述，最大长度1000字符",
                "example": prompt
            },
            "model": {
                "type": "string", 
                "description": "模型名称",
                "example": model,
                "required": True
            }
        },
        "optional_parameters": {
            "mask": {
                "type": "file (binary)",
                "description": "遮罩图像，透明区域指示编辑位置"
            },
            "n": {
                "type": "string",
                "description": "生成图像数量，1-10之间",
                "example": str(n)
            },
            "size": {
                "type": "string",
                "description": "图像尺寸",
                "options": ["256x256", "512x512", "1024x1024"],
                "example": size
            },
            "response_format": {
                "type": "string",
                "description": "返回格式",
                "options": ["url", "b64_json"],
                "example": response_format
            },
            "user": {
                "type": "string",
                "description": "用户标识符"
            }
        },
        "curl_example": f'''curl -X POST "http://localhost:5512/api/gpt/edits" \\
  -F "image=@/path/to/your/image.png" \\
  -F "prompt={prompt}" \\
  -F "model={model}" \\
  -F "n={n}" \\
  -F "size={size}" \\
  -F "response_format={response_format}"''',
        "response_example": {
            "success": True,
            "data": {
                "created": 1589478378,
                "data": [
                    {
                        "url": "https://example.com/edited-image.png"
                    }
                ]
            },
            "request_id": "uuid-string"
        },
        "notes": [
            "图像文件必须是PNG格式，小于4MB，并且是方形的",
            "如果未提供遮罩，图像必须具有透明度作为遮罩",
            "model参数是必需的，目前支持gpt-image-1",
            "可以通过API文档查看更多详情: http://localhost:5512/docs"
        ],
        "alternative_tools": {
            "seededit": "如需基于URL的图像编辑，可使用create_seededit_image工具",
            "command": "create_seededit_image(image_url='your_image_url', prompt='edit_description')"
        }
    }
    
    return json.dumps(api_guide, ensure_ascii=False, indent=2)

async def create_recraft_image_tool(
    prompt: str,
    style: str = "realistic_image",  # 使用文档中正确的默认风格
    size: str = "1024x1024",
    image_format: str = "png"
) -> str:
    """
    创建Recraft图像生成任务
    
    Args:
        prompt: 图像描述提示词，详细描述想要生成的图像内容
        style: 图像风格，默认 realistic_image。支持的风格包括：
            - realistic_image: 真实图片（默认）
            - digital_illustration: 数字插画
            - vector_illustration: 矢量插画
            - realistic_image_mockup: 真实图片模型
            等更多风格，详见API文档
        size: 图像尺寸，默认 1024x1024，支持 WxH 格式
        image_format: 图像格式，支持: png, jpg，默认 png
    
    Returns:
        JSON格式的图像生成结果
    """
    request_id = str(uuid.uuid4())
    
    try:
        service = get_images_service()
        
        result = await service.create_recraft_image(
            prompt=prompt,
            style=style,
            size=size,
            image_format=image_format
        )
        
        # 异步提交图片存储任务（复用FastAPI逻辑）
        submit_image_storage_async(
            request_id=request_id,
            prompt=prompt,
            model="recraft",
            result_data=result,
            generation_params={
                "style": style,
                "size": size,
                "image_format": image_format
            }
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to create Recraft image")
        error_result = {
            "error": True,
            "message": str(e),
            "type": type(e).__name__
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

async def create_seedream_image_tool(
    prompt: str,
    aspect_ratio: str = "1:1",
    negative_prompt: Optional[str] = None,
    cfg_scale: float = 7.5,
    seed: Optional[int] = None
) -> str:
    """
    创建即梦3.0图像生成任务
    
    Args:
        prompt: 图像描述提示词，详细描述想要生成的图像内容
        aspect_ratio: 宽高比，支持: 1:1, 16:9, 9:16, 4:3, 3:4，默认 1:1
        negative_prompt: 负面提示词，描述不想要的内容（可选）
        cfg_scale: CFG缩放值，控制生成与提示词的匹配程度，范围1.0-20.0，默认7.5
        seed: 随机种子，用于复现结果（可选）
    
    Returns:
        JSON格式的图像生成结果
    """
    request_id = str(uuid.uuid4())
    
    try:
        service = get_images_service()
        
        result = await service.create_seedream_image(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            negative_prompt=negative_prompt,
            cfg_scale=cfg_scale,
            seed=seed
        )
        
        # 异步提交图片存储任务（复用FastAPI逻辑）
        submit_image_storage_async(
            request_id=request_id,
            prompt=prompt,
            model="seedream",
            result_data=result,
            generation_params={
                "aspect_ratio": aspect_ratio,
                "negative_prompt": negative_prompt,
                "cfg_scale": cfg_scale,
                "seed": seed
            }
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to create Seedream image")
        error_result = {
            "error": True,
            "message": str(e),
            "type": type(e).__name__
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

async def create_seededit_image_tool(
    image_url: str,
    prompt: str,
    strength: float = 0.8,
    seed: Optional[int] = None,
    model: str = "seededit",
    size: str = "1024x1024"
) -> str:
    """
    创建即梦垫图生成任务 - 基于即梦3.0 (Seedream) API实现图生图功能
    
    Args:
        image_url: 原始图像URL地址，必须是有效的HTTP/HTTPS链接
        prompt: 编辑提示词，描述想要的修改内容
        strength: 编辑强度，范围0.0-1.0，默认 0.8（参数兼容性保留，实际不传递给API）
        seed: 随机种子，用于复现结果（参数兼容性保留，实际不传递给API）
        model: 模型类型参数（兼容性保留，实际使用seedream-3.0模型）
        size: 输出图像尺寸，推荐使用即梦3.0文档建议的尺寸：
               - 1:1 -> 1328x1328 或 1536x1536
               - 4:3 -> 1472x1104
               - 3:2 -> 1584x1056  
               - 16:9 -> 1664x936
               - 21:9 -> 2016x864
    
    Returns:
        JSON格式的图像生成结果
        
    Note:
        - 实际使用即梦3.0 (seedream-3.0) 模型进行图生图
        - prompt格式：将image_url和prompt组合为"URL + 空格 + 编辑指令"
        - 推荐使用1.3K~1.5K分辨率获得更好的画质
    """
    request_id = str(uuid.uuid4())
    
    try:
        service = get_images_service()
        
        result = await service.create_seededit_image(
            image_url=image_url,
            prompt=prompt,
            strength=strength,
            seed=seed,
            model=model,  # 添加model参数
            size=size     # 添加size参数
        )
        
        # 异步提交图片存储任务（复用FastAPI逻辑）
        submit_image_storage_async(
            request_id=request_id,
            prompt=f"{image_url} {prompt}",  # 包含原图URL的提示词
            model="seededit",
            result_data=result,
            generation_params={
                "image_url": image_url,
                "strength": strength,
                "seed": seed,
                "model": model,
                "size": size
            }
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to create SeedEdit image")
        error_result = {
            "error": True,
            "message": str(e),
            "type": type(e).__name__
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

async def create_flux_image_tool(
    prompt: str,
    aspect_ratio: str = "1:1",
    steps: int = 20,
    guidance: float = 7.5,
    seed: Optional[int] = None
) -> str:
    """
    创建FLUX图像生成任务
    
    Args:
        prompt: 图像描述提示词，详细描述想要生成的图像内容
        aspect_ratio: 宽高比，支持: 1:1, 16:9, 9:16, 4:3, 3:4，默认 1:1
        steps: 推理步数，范围1-50，默认 20
        guidance: 引导强度，范围1.0-20.0，默认 7.5
        seed: 随机种子（可选）
    
    Returns:
        JSON格式的图像生成结果
    """
    request_id = str(uuid.uuid4())
    
    try:
        service = get_images_service()
        
        result = await service.create_flux_image(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            steps=steps,
            guidance=guidance,
            seed=seed
        )
        
        # 异步提交图片存储任务（复用FastAPI逻辑）
        submit_image_storage_async(
            request_id=request_id,
            prompt=prompt,
            model="flux",
            result_data=result,
            generation_params={
                "aspect_ratio": aspect_ratio,
                "steps": steps,
                "guidance": guidance,
                "seed": seed
            }
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to create FLUX image")
        error_result = {
            "error": True,
            "message": str(e),
            "type": type(e).__name__
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

# =============================================================================
# 工具函数元信息
# =============================================================================

async def create_stable_diffusion_image_tool(
    prompt: str,
    size: str = "1:1",
    n: int = 1
) -> str:
    """创建StableDiffusion图像生成任务"""
    request_id = str(uuid.uuid4())
    
    try:
        service = get_images_service()
        
        result = await service.create_stable_diffusion_image(
            prompt=prompt,
            size=size,
            n=n
        )
        
        # 异步提交图片存储任务（复用FastAPI逻辑）
        submit_image_storage_async(
            request_id=request_id,
            prompt=prompt,
            model="stable_diffusion",
            result_data=result,
            generation_params={
                "size": size,
                "n": n
            }
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to create StableDiffusion image")
        error_result = {
            "error": True,
            "message": str(e),
            "type": type(e).__name__
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

async def create_hailuo_image_tool(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "standard",
    seed: Optional[int] = None
) -> str:
    """创建海螺图片生成任务"""
    request_id = str(uuid.uuid4())
    
    try:
        service = get_images_service()
        
        result = await service.create_hailuo_image(
            prompt=prompt,
            size=size,
            quality=quality,
            seed=seed
        )
        
        # 异步提交图片存储任务（复用FastAPI逻辑）
        submit_image_storage_async(
            request_id=request_id,
            prompt=prompt,
            model="hailuo",
            result_data=result,
            generation_params={
                "size": size,
                "quality": quality,
                "seed": seed
            }
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to create Hailuo image")
        error_result = {
            "error": True,
            "message": str(e),
            "type": type(e).__name__
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

async def create_doubao_image_tool(
    prompt: str,
    size: str = "1024x1024",
    guidance_scale: int = 3,
    watermark: bool = True
) -> str:
    """创建Doubao图片生成任务"""
    request_id = str(uuid.uuid4())
    
    try:
        service = get_images_service()
        
        result = await service.create_doubao_image(
            prompt=prompt,
            size=size,
            guidance_scale=guidance_scale,
            watermark=watermark
        )
        
        # 异步提交图片存储任务（复用FastAPI逻辑）
        submit_image_storage_async(
            request_id=request_id,
            prompt=prompt,
            model="doubao",
            result_data=result,
            generation_params={
                "size": size,
                "guidance_scale": guidance_scale,
                "watermark": watermark
            }
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to create Doubao image")
        error_result = {
            "error": True,
            "message": str(e),
            "type": type(e).__name__
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

async def create_veo3_video_tool(
    prompt: str,
    model: str = "veo3",
    images: Optional[List[str]] = None,
    enhance_prompt: bool = True
) -> str:
    """
    创建Veo3视频生成任务
    
    Args:
        prompt: 视频描述提示词，详细描述想要生成的视频内容
        model: 模型名称，支持以下选项：
               - veo3: 文生视频 快速版
               - veo3-frames: 图生视频 快速版  
               - veo3-pro: 文生视频 高质量版本
               - veo3-pro-frames: 图生视频 高质量版本
        images: 图像URL列表（图生视频需要，文生视频会忽略）
        enhance_prompt: 是否增强提示词，默认为True
    
    Returns:
        JSON格式的视频生成结果，包含任务ID和状态信息
    """
    request_id = str(uuid.uuid4())
    
    try:
        service = get_images_service()
        
        result = await service.create_veo3_video(
            prompt=prompt,
            model=model,
            images=images,
            enhance_prompt=enhance_prompt
        )
        
        # 如果任务创建成功，添加到视频队列供Celery处理（第三方veo3也是异步的）
        if result.get('id'):
            try:
                # 创建视频任务对象
                video_task = VideoTask(
                    task_id=request_id,
                    external_task_id=result['id'],
                    prompt=prompt,
                    model=model,
                    status="pending",
                    metadata={
                        "images": images,
                        "enhance_prompt": enhance_prompt,
                        "mcp_source": True
                    }
                )
                
                # 添加到任务队列
                if simple_task_queue.add_task(video_task):
                    logger.info(f"[{request_id}] MCP第三方Veo3视频任务已添加到队列，等待Celery处理")
                    
                    # 在响应中添加队列信息
                    result['queue_status'] = 'queued'
                    result['internal_task_id'] = request_id
                    result['mcp_source'] = True
                else:
                    logger.warning(f"[{request_id}] 无法添加第三方Veo3视频任务到队列")
                    
            except Exception as e:
                logger.error(f"[{request_id}] 添加第三方Veo3视频任务到队列失败: {e}")
                # 不影响主要响应，只记录错误
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to create Veo3 video")
        error_result = {
            "error": True,
            "message": str(e),
            "type": type(e).__name__
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

async def get_veo3_task_tool(
    task_id: str
) -> str:
    """
    获取Veo3视频生成任务状态
    
    Args:
        task_id: 任务ID，从创建任务时返回的响应中获取
    
    Returns:
        JSON格式的任务状态信息，包含状态、视频URL等
    """
    try:
        service = get_images_service()
        
        result = await service.get_veo3_task(task_id=task_id)
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to get Veo3 task status")
        error_result = {
            "error": True,
            "message": str(e),
            "type": type(e).__name__
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

# =============================================================================
# 工具函数元信息
# =============================================================================

# 为每个工具函数添加描述信息
create_gpt_image_tool.__doc__ = """创建GPT图像生成任务 - 使用gpt-image-1模型根据文本描述生成图像"""
create_recraft_image_tool.__doc__ = """创建Recraft图像生成任务 - 专业的图像创作工具"""
create_seedream_image_tool.__doc__ = """创建即梦3.0图像生成任务 - 先进的图像生成技术"""
create_seededit_image_tool.__doc__ = """创建即梦垫图生成任务 - 基于现有图像的智能编辑"""
create_flux_image_tool.__doc__ = """创建FLUX图像生成任务 - 高质量的开源图像生成模型"""
create_stable_diffusion_image_tool.__doc__ = """创建StableDiffusion图像生成任务 - 经典的开源图像生成模型"""
create_hailuo_image_tool.__doc__ = """创建海螺图片生成任务 - 海螺AI的图像生成"""
create_doubao_image_tool.__doc__ = """创建Doubao图片生成任务 - 字节跳动的图像生成"""
create_veo3_video_tool.__doc__ = """创建Veo3视频生成任务 - Google Veo3模型的视频生成功能"""
get_veo3_task_tool.__doc__ = """获取Veo3视频生成任务状态 - 查询任务进度和获取视频结果"""

# =============================================================================
# 文件上传工具函数
# =============================================================================

async def upload_image_file_tool(
    file_description: str,
    folder: str = "uploads"
) -> str:
    """
    上传图片文件工具
    
    Args:
        file_description: 图片文件描述（用于提示）
        folder: 存储文件夹名称，默认为uploads
    
    Returns:
        提示信息，告知AI如何使用实际的文件上传API
    """
    try:
        # 返回提示信息，指导AI如何使用实际的API
        base_url = settings.server.base_url
        instruction = {
            "message": "这是一个虚构的图片上传接口。要实现图片上传功能，请使用以下实际的API：",
            "api_info": {
                "endpoint": "POST /api/files/upload",
                "base_url": base_url,
                "description": "文件上传API接口，支持图片文件上传到MinIO对象存储",
                "parameters": {
                    "file": "要上传的图片文件（multipart/form-data）",
                    "folder": f"存储文件夹（可选，默认为uploads，当前指定：{folder}）"
                },
                "response_fields": {
                    "direct_url": "直接访问图片的URL（可在浏览器中直接打开）",
                    "access_url": "兼容性访问URL",
                    "image_url": "图片专用访问URL",
                    "object_name": "在存储中的对象名称",
                    "file_size": "文件大小（字节）",
                    "file_hash": "文件哈希值",
                    "upload_time": "上传时间"
                }
            },
            "usage_example": {
                "curl_command": f"curl -X POST '{base_url}/api/files/upload' -F 'file=@/path/to/image.png' -F 'folder={folder}'",
                "javascript_fetch": f"""
fetch('{base_url}/api/files/upload', {{
    method: 'POST',
    body: formData  // FormData with file and folder
}})
.then(response => response.json())
.then(data => {{
    console.log('图片上传成功:', data.data.direct_url);
}});
"""
            },
            "notes": [
                "上传成功后，可通过返回的direct_url直接在浏览器中查看图片",
                "支持的图片格式：PNG, JPG, JPEG, GIF, WebP等",
                "文件会自动生成唯一的文件名以避免冲突",
                f"返回的URL格式：{base_url}/api/images/" + "{object_name}"
            ],
            "requested_info": {
                "file_description": file_description,
                "target_folder": folder
            }
        }
        
        return json.dumps(instruction, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to provide upload image instruction")
        error_result = {
            "error": True,
            "message": "无法提供图片上传指导信息",
            "details": str(e),
            "type": type(e).__name__
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

# 为上传工具添加描述信息
upload_image_file_tool.__doc__ = """上传图片文件工具 - 提供图片上传API的使用指导"""



# =============================================================================
# Google Vertex AI 官方Veo3视频生成工具函数
# =============================================================================

async def create_veo3_official_video_tool(
    prompt: str,
    duration: int = 5,
    aspect_ratio: str = "16:9",
    wait_for_completion: bool = False,
    max_wait: int = 600,
    seed: Optional[int] = None,
    guidance_scale: Optional[float] = None,
    negative_prompt: Optional[str] = None
) -> str:
    """
    创建Google Vertex AI官方Veo3视频生成任务
    
    Args:
        prompt: 视频描述提示词，详细描述想要生成的视频内容
        duration: 视频时长(秒)，范围1-30，默认5秒
        aspect_ratio: 宽高比，支持16:9, 9:16, 1:1, 4:3, 3:4，默认16:9
        wait_for_completion: 是否等待完成，True时会等待任务完成后返回结果，默认False
        max_wait: 最大等待时间(秒)，范围60-1800，默认600秒
        seed: 随机种子，用于复现结果
        guidance_scale: 引导缩放值，控制生成与提示词的匹配程度
        negative_prompt: 负面提示词，描述不想要的内容
    
    Returns:
        JSON格式的视频生成结果，包含operation_id和状态信息
    """
    request_id = str(uuid.uuid4())
    
    try:
        service = get_images_service()
        
        # 构建额外参数
        kwargs = {}
        if seed is not None:
            kwargs['seed'] = seed
        if guidance_scale is not None:
            kwargs['guidanceScale'] = guidance_scale
        if negative_prompt:
            kwargs['negativePrompt'] = negative_prompt
        
        result = await service.create_veo3_official_video(
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            wait_for_completion=False,  # 强制异步模式，复用FastAPI逻辑
            max_wait=60,  # 设置默认值
            **kwargs
        )
        
        # 如果任务创建成功，添加到视频队列供Celery处理（复用FastAPI逻辑）
        if result.get('operation_id'):
            try:
                # 创建视频任务对象
                video_task = VideoTask(
                    task_id=request_id,
                    external_task_id=result['operation_id'],
                    prompt=prompt,
                    model="veo3-official",
                    status="pending",
                    metadata={
                        "duration": duration,
                        "aspect_ratio": aspect_ratio,
                        "guidance_scale": guidance_scale,
                        "seed": seed,
                        "negative_prompt": negative_prompt,
                        "mcp_source": True
                    }
                )
                
                # 添加到任务队列
                if simple_task_queue.add_task(video_task):
                    logger.info(f"[{request_id}] MCP视频任务已添加到队列，等待Celery处理")
                    
                    # 在响应中添加队列信息
                    result['queue_status'] = 'queued'
                    result['internal_task_id'] = request_id
                    result['mcp_source'] = True
                else:
                    logger.warning(f"[{request_id}] 无法添加视频任务到队列")
                    
            except Exception as e:
                logger.error(f"[{request_id}] 添加视频任务到队列失败: {e}")
                # 不影响主要响应，只记录错误
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to create Vertex AI Veo3 video")
        error_result = {
            "error": True,
            "message": str(e),
            "type": type(e).__name__,
            "service": "Google Vertex AI Veo3"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

async def check_veo3_official_status_tool(
    operation_id: str
) -> str:
    """
    检查Google Vertex AI官方Veo3任务状态
    
    Args:
        operation_id: 任务操作ID，从创建任务时返回
    
    Returns:
        JSON格式的任务状态信息，包含状态、数据等
    """
    try:
        service = get_images_service()
        
        result = await service.check_veo3_official_status(operation_id)
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to check Vertex AI Veo3 status")
        error_result = {
            "error": True,
            "message": str(e),
            "type": type(e).__name__,
            "service": "Google Vertex AI Veo3"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

# 为Vertex AI Veo3工具添加描述信息
create_veo3_official_video_tool.__doc__ = """创建Google Vertex AI官方Veo3视频生成任务 - 使用Google官方API直接调用Vertex AI的Veo3模型（纯异步模式）"""
check_veo3_official_status_tool.__doc__ = """检查Google Vertex AI官方Veo3任务状态 - 查询长时间运行操作的当前状态（异步轮询）"""