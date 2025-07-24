#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Images API MCP 工具函数

为 MCP 协议提供 Images API 功能封装
"""

from typing import Dict, List, Optional, Any, Union
import json

from services.images_service import get_images_service
from core.images_client import ImagesAPIError
from core.logger import get_mcp_logger, log_exception
from core.config import settings

logger = get_mcp_logger()

# =============================================================================
# MCP 工具函数实现
# =============================================================================

async def create_gpt_image_tool(
    prompt: str,
    model: str = "dall-e-3",
    n: int = 1,
    size: str = "1024x1024",
    quality: str = "standard",
    style: str = "vivid"
) -> str:
    """
    创建GPT图像生成任务
    
    Args:
        prompt: 图像描述提示词，详细描述想要生成的图像内容
        model: 模型名称，支持: dall-e-3, dall-e-2，默认 dall-e-3
        n: 生成图像数量，dall-e-3最多1张，dall-e-2最多10张，默认 1
        size: 图像尺寸，支持多种规格，默认 1024x1024
        quality: 图像质量，支持: standard, hd，默认 standard
        style: 图像风格，支持: vivid, natural，默认 vivid
    
    Returns:
        JSON格式的图像生成结果，包含图像URL和相关信息
    """
    try:
        service = get_images_service()
        
        result = await service.create_gpt_image(
            prompt=prompt,
            model=model,
            n=n,
            size=size,
            quality=quality,
            style=style
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to create GPT image")
        error_message = str(e) if str(e).strip() else f"Unexpected error in GPT image generation: {type(e).__name__}"
        error_result = {
            "error": True,
            "message": error_message,
            "type": type(e).__name__
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

async def create_gpt_image_edit_tool(
    image_url: str,
    prompt: str,
    mask_url: Optional[str] = None,
    n: str = "1",
    size: str = "1024x1024",
    response_format: str = "url"
) -> str:
    """
    创建GPT图像编辑任务
    
    在给定原始图像和提示的情况下创建编辑或扩展图像
    
    Args:
        image_url: 要编辑的图像URL地址，必须是有效的PNG文件，小于4MB，方形
        prompt: 所需图像的文本描述，最大长度为1000个字符
        mask_url: 可选的遮罩图像URL，透明区域指示要编辑的位置
        n: 要生成的图像数，必须介于1和10之间
        size: 生成图像的大小，必须是256x256、512x512或1024x1024之一
        response_format: 生成的图像返回格式，必须是url或b64_json
    
    Returns:
        JSON格式的图像编辑结果，包含编辑后的图像URL和相关信息
    """
    try:
        service = get_images_service()
        
        result = await service.create_gpt_image_edit(
            image=image_url,
            prompt=prompt,
            mask=mask_url,
            n=n,
            size=size,
            response_format=response_format
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except ImagesAPIError as e:
        logger.error(f"GPT image edit API error: {e}")
        error_result = {
            "error": True,
            "message": e.message,
            "status_code": e.status_code,
            "error_code": e.error_code
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to create GPT image edit")
        error_message = str(e) if str(e).strip() else f"Unexpected error in GPT image edit: {type(e).__name__}"
        error_result = {
            "error": True,
            "message": error_message,
            "type": type(e).__name__
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

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
    try:
        service = get_images_service()
        
        result = await service.create_recraft_image(
            prompt=prompt,
            style=style,
            size=size,
            image_format=image_format
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to create Recraft image")
        error_message = str(e) if str(e).strip() else f"Unexpected error in Recraft image generation: {type(e).__name__}"
        error_result = {
            "error": True,
            "message": error_message,
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
    try:
        service = get_images_service()
        
        result = await service.create_seedream_image(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            negative_prompt=negative_prompt,
            cfg_scale=cfg_scale,
            seed=seed
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to create Seedream image")
        error_message = str(e) if str(e).strip() else f"Unexpected error in Seedream image generation: {type(e).__name__}"
        error_result = {
            "error": True,
            "message": error_message,
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
    创建即梦垫图生成任务 - 基于现有图像进行智能编辑
    
    Args:
        image_url: 原始图像URL地址，必须是有效的HTTP/HTTPS链接
        prompt: 编辑提示词，描述想要的修改内容
        strength: 编辑强度，范围0.0-1.0，默认 0.8（仅作为可选参数，API可能不支持）
        seed: 随机种子，用于复现结果（可选）
        model: 模型类型，支持 "seededit" 或 "seededit-pro"，默认 "seededit"
        size: 输出图像尺寸，格式如 "1024x1024"，默认 "1024x1024"
    
    Returns:
        JSON格式的图像生成结果
        
    Note:
        根据API文档，该接口会将image_url和prompt组合成最终的prompt格式
    """
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
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to create SeedEdit image")
        error_message = str(e) if str(e).strip() else f"Unexpected error in SeedEdit image editing: {type(e).__name__}"
        error_result = {
            "error": True,
            "message": error_message,
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
    try:
        service = get_images_service()
        
        result = await service.create_flux_image(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            steps=steps,
            guidance=guidance,
            seed=seed
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to create FLUX image")
        error_message = str(e) if str(e).strip() else f"Unexpected error in FLUX image generation: {type(e).__name__}"
        error_result = {
            "error": True,
            "message": error_message,
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
    try:
        service = get_images_service()
        
        result = await service.create_stable_diffusion_image(
            prompt=prompt,
            size=size,
            n=n
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to create StableDiffusion image")
        error_message = str(e) if str(e).strip() else f"Unexpected error in StableDiffusion image generation: {type(e).__name__}"
        error_result = {
            "error": True,
            "message": error_message,
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
    try:
        service = get_images_service()
        
        result = await service.create_hailuo_image(
            prompt=prompt,
            size=size,
            quality=quality,
            seed=seed
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to create Hailuo image")
        error_message = str(e) if str(e).strip() else f"Unexpected error in Hailuo image generation: {type(e).__name__}"
        error_result = {
            "error": True,
            "message": error_message,
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
    try:
        service = get_images_service()
        
        result = await service.create_doubao_image(
            prompt=prompt,
            size=size,
            guidance_scale=guidance_scale,
            watermark=watermark
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_exception(logger, e, "Failed to create Doubao image")
        error_message = str(e) if str(e).strip() else f"Unexpected error in Doubao image generation: {type(e).__name__}"
        error_result = {
            "error": True,
            "message": error_message,
            "type": type(e).__name__
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

# =============================================================================
# 工具函数元信息
# =============================================================================

# 为每个工具函数添加描述信息
create_gpt_image_tool.__doc__ = """创建GPT图像生成任务 - 使用DALL-E模型根据文本描述生成图像"""
create_recraft_image_tool.__doc__ = """创建Recraft图像生成任务 - 专业的图像创作工具"""
create_seedream_image_tool.__doc__ = """创建即梦3.0图像生成任务 - 先进的图像生成技术"""
create_seededit_image_tool.__doc__ = """创建即梦垫图生成任务 - 基于现有图像的智能编辑"""
create_flux_image_tool.__doc__ = """创建FLUX图像生成任务 - 高质量的开源图像生成模型"""
create_stable_diffusion_image_tool.__doc__ = """创建StableDiffusion图像生成任务 - 经典的开源图像生成模型"""
create_hailuo_image_tool.__doc__ = """创建海螺图片生成任务 - 海螺AI的图像生成"""
create_doubao_image_tool.__doc__ = """创建Doubao图片生成任务 - 字节跳动的图像生成"""

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