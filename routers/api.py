#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Images API FastAPI 路由

提供 RESTful API 接口，支持多种图像生成模型
"""

from fastapi import APIRouter, HTTPException, Header, Query, Depends, UploadFile, File
from fastapi.responses import RedirectResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
import uuid
from datetime import datetime

from services.images_service import get_images_service, ImagesService
from core.images_client import ImagesAPIError
from core.minio_client import get_minio_client, MinIOClient, MinIOError
from core.logger import get_api_logger, log_exception
from core.config import settings
from core.simple_task_queue import simple_task_queue, VideoTask

logger = get_api_logger()
router = APIRouter()

# =============================================================================
# 异步存储辅助函数
# =============================================================================

def submit_image_storage_async(
    request_id: str,
    prompt: str,
    model: str,
    result_data: Any,
    generation_params: Optional[Dict[str, Any]] = None
):
    """
    异步提交图片存储任务（KISS原则：简单直接）
    
    Args:
        request_id: API请求ID
        prompt: 生成提示词
        model: 使用的模型
        result_data: API返回的结果数据
        generation_params: 生成参数
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
            
            celery_task_id = submit_image_storage_task(
                request_id=request_id,
                prompt=prompt,
                model=model,
                image_urls=image_urls,
                generation_params=generation_params
            )
            
            logger.info(f"[{request_id}] 异步图片存储任务已提交: {celery_task_id}")
            return celery_task_id
        else:
            logger.warning(f"[{request_id}] 未找到可存储的图片URL")
            return None
            
    except Exception as e:
        # 存储失败不应该影响API主要响应
        logger.error(f"[{request_id}] 异步图片存储提交失败: {e}")
        return None

# =============================================================================
# 请求/响应模型
# =============================================================================

class ImagesBaseRequest(BaseModel):
    """Images API 基础请求模型"""
    pass

class GPTImageRequest(ImagesBaseRequest):
    """GPT图像生成请求"""
    prompt: str = Field(..., description="图像描述提示词，详细描述想要生成的图像内容")
    model: str = Field(default="gpt-image-1", description="模型名称，固定为: gpt-image-1")
    n: int = Field(default=1, description="生成图像数量，dall-e-3最多1张，dall-e-2最多10张")
    size: str = Field(default="1024x1024", description="图像尺寸，支持多种规格")
    quality: Optional[str] = Field(default=None, description="图像质量，gpt-image-1模型不支持此参数")
    style: str = Field(default="vivid", description="图像风格，支持: vivid, natural")

class RecraftImageRequest(ImagesBaseRequest):
    """Recraft图像生成请求"""
    prompt: str = Field(..., description="图像描述提示词")
    style: str = Field(default="realistic", description="图像风格")
    size: str = Field(default="1024x1024", description="图像尺寸")
    image_format: str = Field(default="png", description="图像格式，支持: png, jpg")

class SeedreamImageRequest(ImagesBaseRequest):
    """即梦3.0图像生成请求"""
    prompt: str = Field(..., description="图像描述提示词")
    aspect_ratio: str = Field(default="1:1", description="宽高比，支持: 1:1, 16:9, 9:16, 4:3, 3:4")
    negative_prompt: Optional[str] = Field(None, description="负面提示词，描述不想要的内容")
    cfg_scale: float = Field(default=7.5, description="CFG缩放值，控制生成与提示词的匹配程度，范围1.0-20.0")
    seed: Optional[int] = Field(None, description="随机种子，用于复现结果")

class SeedEditImageRequest(ImagesBaseRequest):
    """即梦垫图生成请求"""
    image_url: str = Field(..., description="原始图像URL地址")
    prompt: str = Field(..., description="编辑提示词，描述想要的修改")
    strength: float = Field(default=0.8, description="编辑强度，范围0.0-1.0")
    seed: Optional[int] = Field(None, description="随机种子")

class FluxImageRequest(ImagesBaseRequest):
    """FLUX图像创建请求"""
    prompt: str = Field(..., description="图像描述提示词")
    aspect_ratio: str = Field(default="1:1", description="宽高比，支持: 1:1, 16:9, 9:16, 4:3, 3:4")
    steps: int = Field(default=20, description="推理步数，范围1-50")
    guidance: float = Field(default=7.5, description="引导强度，范围1.0-20.0")
    seed: Optional[int] = Field(None, description="随机种子")

class ImagesAPIResponse(BaseModel):
    """Images API 统一响应格式"""
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class Veo3VideoRequest(BaseModel):
    """Veo3视频生成请求"""
    prompt: str = Field(..., description="视频描述提示词")
    model: str = Field(default="veo3", description="模型名称 (veo3, veo3-frames, veo3-pro, veo3-pro-frames)")
    images: Optional[List[str]] = Field(default=None, description="图像URL列表（图生视频需要，文生视频会忽略）")
    enhance_prompt: bool = Field(default=True, description="是否增强提示词")

# =============================================================================
# 依赖注入
# =============================================================================

def get_service() -> ImagesService:
    """获取 Images 服务实例"""
    return get_images_service()

def get_storage() -> MinIOClient:
    """获取 MinIO 存储客户端实例"""
    return get_minio_client()


# =============================================================================
# API 路由
# =============================================================================

@router.post("/gpt/generations", response_model=ImagesAPIResponse)
async def create_gpt_image(
    request: GPTImageRequest,
    service: ImagesService = Depends(get_service)
):
    """
    GPT图像生成接口
    
    支持DALL-E 2和DALL-E 3模型，根据文本描述生成高质量图像
    """
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Creating GPT image generation task")
        
        # 构建请求参数，排除None值
        kwargs = {
            "prompt": request.prompt,
            "model": request.model,
            "n": request.n,
            "size": request.size
        }
        if request.quality is not None:
            kwargs["quality"] = request.quality
        
        result = await service.create_gpt_image(**kwargs)
        
        # 自动上传生成的图片到素材库
        if result and result.get('data'):
            try:
                # result['data'] is directly the images list for GPT API
                images = result['data'] if isinstance(result['data'], list) else [result['data']]
                for i, image_data in enumerate(images):
                    if image_data.get('url'):
                        material_info = await material_mgr.upload_sync_material(
                            material_url=image_data['url'],
                            material_type="image",
                            model=request.model,
                            user_id=request_id,  # 使用request_id作为临时用户ID
                            prompt=request.prompt,
                            generation_params={
                                "n": request.n,
                                "size": request.size,
                                "quality": request.quality
                            },
                            api_response=result,
                            tags=["gpt", "dall-e", "generated"],
                            description=f"GPT {request.model}生成的图片: {request.prompt[:100]}..."
                        )
                        
                        if material_info:
                            # 添加素材库信息到响应中
                            image_data['material_info'] = {
                                "material_id": material_info.material_id,
                                "minio_path": material_info.minio_path,
                                "thumbnail_path": material_info.thumbnail_path,
                                "uploaded_at": material_info.created_at
                            }
                            logger.info(f"[{request_id}] Image {i+1} uploaded to material library: {material_info.material_id}")
                        else:
                            logger.warning(f"[{request_id}] Failed to upload image {i+1} to material library")
                            
            except Exception as e:
                logger.warning(f"[{request_id}] Failed to upload materials to library: {e}")
                # 不影响主要响应，只记录警告
        
        # 异步提交图片存储任务（KISS原则：在返回响应前异步提交）
        submit_image_storage_async(
            request_id=request_id,
            prompt=request.prompt,
            model=request.model,
            result_data=result,
            generation_params={
                "n": request.n,
                "size": request.size,
                "quality": request.quality
            }
        )
        
        return ImagesAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except ValueError as e:
        logger.warning(f"[{request_id}] Invalid request parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except ImagesAPIError as e:
        log_exception(logger, e, f"[{request_id}] Images API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/gpt/edits", response_model=ImagesAPIResponse)
async def create_gpt_image_edit(
    image: UploadFile = File(..., description="要编辑的图像，必须是有效的PNG文件，小于4MB，方形"),
    prompt: str = Query(..., description="所需图像的文本描述，最大长度为1000个字符"),
    mask: Optional[UploadFile] = File(None, description="可选的遮罩图像，透明区域指示要编辑的位置"),
    n: str = Query(default="1", description="要生成的图像数，必须介于1和10之间"),
    size: str = Query(default="1024x1024", description="生成图像的大小，必须是256x256、512x512或1024x1024之一"),
    response_format: str = Query(default="url", description="生成的图像返回格式，必须是url或b64_json"),
    service: ImagesService = Depends(get_service)
):
    """
    GPT图像编辑接口
    
    在给定原始图像和提示的情况下创建编辑或扩展图像
    """
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Creating GPT image edit task")
        
        # 读取图像文件
        image_content = await image.read()
        
        # 读取遮罩文件（如果提供）
        mask_content = None
        if mask:
            mask_content = await mask.read()
        
        result = await service.create_gpt_image_edit(
            image=image_content,
            prompt=prompt,
            mask=mask_content,
            n=n,
            size=size,
            response_format=response_format
        )
        
        return ImagesAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except ValueError as e:
        logger.warning(f"[{request_id}] Invalid request parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except ImagesAPIError as e:
        log_exception(logger, e, f"[{request_id}] Images API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/recraft/generate", response_model=ImagesAPIResponse)
async def create_recraft_image(
    request: RecraftImageRequest,
    service: ImagesService = Depends(get_service)
):
    """
    Recraft图像生成接口
    
    专业的图像创作工具，支持多种艺术风格
    """
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Creating Recraft image generation task")
        
        result = await service.create_recraft_image(
            prompt=request.prompt,
            style=request.style,
            size=request.size,
            image_format=request.image_format
        )
        
        # 自动上传生成的图片到素材库
        if result and result.get('data'):
            try:
                # result['data'] is directly the images list for Recraft API too
                images = result['data'] if isinstance(result['data'], list) else [result['data']]
                for i, image_data in enumerate(images):
                    if image_data.get('url'):
                        material_info = await material_mgr.upload_sync_material(
                            material_url=image_data['url'],
                            material_type="image",
                            model="recraft",
                            user_id=request_id,
                            prompt=request.prompt,
                            generation_params={
                                "style": request.style,
                                "size": request.size,
                                "image_format": request.image_format
                            },
                            api_response=result,
                            tags=["recraft", "professional", "generated"],
                            description=f"Recraft生成的专业图片: {request.prompt[:100]}..."
                        )
                        
                        if material_info:
                            image_data['material_info'] = {
                                "material_id": material_info.material_id,
                                "minio_path": material_info.minio_path,
                                "thumbnail_path": material_info.thumbnail_path,
                                "uploaded_at": material_info.created_at
                            }
                            logger.info(f"[{request_id}] Image {i+1} uploaded to material library: {material_info.material_id}")
                        else:
                            logger.warning(f"[{request_id}] Failed to upload image {i+1} to material library")
                            
            except Exception as e:
                logger.warning(f"[{request_id}] Failed to upload materials to library: {e}")
        
        # 异步提交图片存储任务（KISS原则：在返回响应前异步提交）
        submit_image_storage_async(
            request_id=request_id,
            prompt=request.prompt,
            model="recraft",
            result_data=result,
            generation_params={
                "style": request.style,
                "size": request.size,
                "image_format": request.image_format
            }
        )
        
        return ImagesAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except ValueError as e:
        logger.warning(f"[{request_id}] Invalid request parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except ImagesAPIError as e:
        log_exception(logger, e, f"[{request_id}] Images API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/seedream/generate", response_model=ImagesAPIResponse)
async def create_seedream_image(
    request: SeedreamImageRequest,
    service: ImagesService = Depends(get_service)
):
    """
    即梦3.0图像生成接口
    
    先进的图像生成技术，支持精确的提示词控制
    """
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Creating Seedream image generation task")
        
        result = await service.create_seedream_image(
            prompt=request.prompt,
            aspect_ratio=request.aspect_ratio,
            negative_prompt=request.negative_prompt,
            cfg_scale=request.cfg_scale,
            seed=request.seed
        )
        
        # 异步提交图片存储任务（KISS原则：在返回响应前异步提交）
        submit_image_storage_async(
            request_id=request_id,
            prompt=request.prompt,
            model="seedream",
            result_data=result,
            generation_params={
                "aspect_ratio": request.aspect_ratio,
                "negative_prompt": request.negative_prompt,
                "cfg_scale": request.cfg_scale,
                "seed": request.seed
            }
        )
        
        return ImagesAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except ValueError as e:
        logger.warning(f"[{request_id}] Invalid request parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except ImagesAPIError as e:
        log_exception(logger, e, f"[{request_id}] Images API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/seededit/generate", response_model=ImagesAPIResponse)
async def create_seededit_image(
    request: SeedEditImageRequest,
    service: ImagesService = Depends(get_service)
):
    """
    即梦垫图生成接口
    
    基于现有图像进行智能编辑和优化
    """
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Creating SeedEdit image generation task")
        
        result = await service.create_seededit_image(
            image_url=request.image_url,
            prompt=request.prompt,
            strength=request.strength,
            seed=request.seed
        )
        
        # 异步提交图片存储任务（KISS原则：在返回响应前异步提交）
        submit_image_storage_async(
            request_id=request_id,
            prompt=request.prompt,
            model="seededit",
            result_data=result,
            generation_params={
                "image_url": request.image_url,
                "strength": request.strength,
                "seed": request.seed
            }
        )
        
        return ImagesAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except ValueError as e:
        logger.warning(f"[{request_id}] Invalid request parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except ImagesAPIError as e:
        log_exception(logger, e, f"[{request_id}] Images API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/flux/create", response_model=ImagesAPIResponse)
async def create_flux_image(
    request: FluxImageRequest,
    service: ImagesService = Depends(get_service)
):
    """
    FLUX图像创建接口
    
    高质量的开源图像生成模型
    """
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Creating FLUX image generation task")
        
        result = await service.create_flux_image(
            prompt=request.prompt,
            aspect_ratio=request.aspect_ratio,
            steps=request.steps,
            guidance=request.guidance,
            seed=request.seed
        )
        
        # 异步提交图片存储任务（KISS原则：在返回响应前异步提交）
        submit_image_storage_async(
            request_id=request_id,
            prompt=request.prompt,
            model="flux",
            result_data=result,
            generation_params={
                "aspect_ratio": request.aspect_ratio,
                "steps": request.steps,
                "guidance": request.guidance,
                "seed": request.seed
            }
        )
        
        return ImagesAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except ValueError as e:
        logger.warning(f"[{request_id}] Invalid request parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except ImagesAPIError as e:
        log_exception(logger, e, f"[{request_id}] Images API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

# =============================================================================
# 健康检查
# =============================================================================

# 继续添加剩余API端点
@router.post("/recraftv3/create", response_model=ImagesAPIResponse)
async def create_recraftv3_image(
    request: RecraftImageRequest,
    service: ImagesService = Depends(get_service)
):
    """Recraftv3图像创建接口"""
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Creating Recraftv3 image generation task")
        
        result = await service.create_recraftv3_image(
            prompt=request.prompt,
            style=request.style,
            size=request.size,
            image_format=request.image_format
        )
        
        return ImagesAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except ValueError as e:
        logger.warning(f"[{request_id}] Invalid request parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except ImagesAPIError as e:
        log_exception(logger, e, f"[{request_id}] Images API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

class CogviewImageRequest(ImagesBaseRequest):
    """Cogview图像创建请求"""
    prompt: str = Field(..., description="图像描述提示词")
    size: str = Field(default="1024x1024", description="图像尺寸")
    quality: str = Field(default="standard", description="图像质量")
    seed: Optional[int] = Field(None, description="随机种子")

@router.post("/cogview/create", response_model=ImagesAPIResponse)
async def create_cogview_image(
    request: CogviewImageRequest,
    service: ImagesService = Depends(get_service)
):
    """Cogview图像创建接口"""
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Creating Cogview image generation task")
        
        result = await service.create_cogview_image(
            prompt=request.prompt,
            size=request.size,
            quality=request.quality,
            seed=request.seed
        )
        
        return ImagesAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except ValueError as e:
        logger.warning(f"[{request_id}] Invalid request parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except ImagesAPIError as e:
        log_exception(logger, e, f"[{request_id}] Images API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

class HunyuanImageRequest(ImagesBaseRequest):
    """混元图像创建请求"""
    prompt: str = Field(..., description="图像描述提示词")
    aspect_ratio: str = Field(default="1:1", description="宽高比")
    seed: Optional[int] = Field(None, description="随机种子")

@router.post("/hunyuan/create", response_model=ImagesAPIResponse)
async def create_hunyuan_image(
    request: HunyuanImageRequest,
    service: ImagesService = Depends(get_service)
):
    """混元图像创建接口"""
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Creating Hunyuan image generation task")
        
        result = await service.create_hunyuan_image(
            prompt=request.prompt,
            aspect_ratio=request.aspect_ratio,
            seed=request.seed
        )
        
        return ImagesAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except ValueError as e:
        logger.warning(f"[{request_id}] Invalid request parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except ImagesAPIError as e:
        log_exception(logger, e, f"[{request_id}] Images API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

class KlingImageRequest(ImagesBaseRequest):
    """Kling图像创建请求"""
    prompt: str = Field(..., description="图像描述提示词")
    aspect_ratio: str = Field(default="1:1", description="宽高比")
    negative_prompt: Optional[str] = Field(None, description="负面提示词")
    cfg_scale: float = Field(default=7.5, description="CFG缩放值")
    seed: Optional[int] = Field(None, description="随机种子")

@router.post("/kling/create", response_model=ImagesAPIResponse)
async def create_kling_image(
    request: KlingImageRequest,
    service: ImagesService = Depends(get_service)
):
    """Kling图像创建接口"""
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Creating Kling image generation task")
        
        result = await service.create_kling_image(
            prompt=request.prompt,
            aspect_ratio=request.aspect_ratio,
            negative_prompt=request.negative_prompt,
            cfg_scale=request.cfg_scale,
            seed=request.seed
        )
        
        return ImagesAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except ValueError as e:
        logger.warning(f"[{request_id}] Invalid request parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except ImagesAPIError as e:
        log_exception(logger, e, f"[{request_id}] Images API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

# =============================================================================
# 文件上传和存储 API
# =============================================================================

class FileUploadResponse(BaseModel):
    """文件上传响应"""
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

@router.post("/files/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    folder: str = Query(default="uploads", description="存储文件夹"),
    storage: MinIOClient = Depends(get_storage)
):
    """
    文件上传接口
    
    支持图片文件上传到MinIO对象存储，自动生成访问URL
    """
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Uploading file: {file.filename}")
        
        # 上传文件到MinIO
        result = await storage.upload_file(
            file=file,
            folder=folder
        )
        
        # 生成直接可访问的图片URL（无需重定向）
        object_name = result['object_name']
        direct_url = f"{settings.server.base_url}/api/images/{object_name}"
        
        # 更新返回结果，使用直接访问的图片URL
        result['direct_url'] = direct_url
        result['access_url'] = direct_url  # 兼容性字段
        result['image_url'] = direct_url   # 图片专用字段
        
        logger.info(f"[{request_id}] File uploaded successfully: {result['object_name']}")
        logger.info(f"[{request_id}] Direct access URL: {direct_url}")
        
        return FileUploadResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except MinIOError as e:
        logger.warning(f"[{request_id}] MinIO error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error during file upload")
        raise HTTPException(status_code=500, detail="文件上传失败")

@router.get("/images/{object_name:path}")
async def get_image_direct(
    object_name: str,
    storage: MinIOClient = Depends(get_storage)
):
    """
    直接返回图片内容
    
    不进行重定向，直接从MinIO读取并返回图片数据
    """
    try:
        # 检查文件是否存在
        file_info = await storage.get_file_info(object_name)
        if not file_info:
            raise HTTPException(status_code=404, detail="图片不存在")
        
        # 从MinIO直接获取文件流
        file_data = await storage.get_file_stream(object_name)
        
        # 获取内容类型
        content_type = file_info.get('content_type', 'application/octet-stream')
        
        # 返回流式响应
        return StreamingResponse(
            file_data,
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename={object_name.split('/')[-1]}",
                "Cache-Control": "public, max-age=3600"  # 缓存1小时
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_exception(logger, e, f"Unexpected error serving image: {object_name}")
        raise HTTPException(status_code=500, detail="获取图片失败")

@router.get("/files/{object_name:path}/redirect")
async def redirect_to_file(
    object_name: str,
    expires_hours: int = Query(default=1, description="URL过期时间(小时)", ge=1, le=24),
    storage: MinIOClient = Depends(get_storage)
):
    """
    直接重定向到文件URL
    
    用于需要直接访问文件的场景
    """
    try:
        # 检查文件是否存在
        file_info = await storage.get_file_info(object_name)
        if not file_info:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 生成预签名URL并重定向
        file_url = await storage.get_presigned_url(object_name, expires_hours)
        
        return RedirectResponse(url=file_url, status_code=302)
        
    except HTTPException:
        raise
    except MinIOError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"Unexpected error redirecting to file: {object_name}")
        raise HTTPException(status_code=500, detail="文件重定向失败")

@router.get("/files/{object_name:path}")
async def get_file_url(
    object_name: str,
    expires_hours: int = Query(default=24, description="URL过期时间(小时)", ge=1, le=168),
    storage: MinIOClient = Depends(get_storage)
):
    """
    获取文件访问URL
    
    返回MinIO对象的预签名访问URL
    """
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Generating URL for object: {object_name}")
        
        # 检查文件是否存在
        file_info = await storage.get_file_info(object_name)
        if not file_info:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 生成预签名URL
        file_url = await storage.get_presigned_url(object_name, expires_hours)
        
        return {
            "success": True,
            "data": {
                "object_name": object_name,
                "file_url": file_url,
                "expires_hours": expires_hours,
                "file_info": file_info
            },
            "request_id": request_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except MinIOError as e:
        logger.warning(f"[{request_id}] MinIO error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error getting file URL")
        raise HTTPException(status_code=500, detail="获取文件URL失败")

@router.delete("/files/{object_name:path}")
async def delete_file(
    object_name: str,
    storage: MinIOClient = Depends(get_storage)
):
    """
    删除文件
    
    从MinIO对象存储中删除指定文件
    """
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Deleting object: {object_name}")
        
        # 检查文件是否存在
        file_info = await storage.get_file_info(object_name)
        if not file_info:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 删除文件
        success = await storage.delete_file(object_name)
        
        return {
            "success": success,
            "data": {
                "object_name": object_name,
                "deleted": True
            },
            "request_id": request_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except MinIOError as e:
        logger.warning(f"[{request_id}] MinIO error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error deleting file")
        raise HTTPException(status_code=500, detail="文件删除失败")

@router.get("/files")
async def list_files(
    prefix: str = Query(default="", description="路径前缀"),
    limit: int = Query(default=100, description="返回数量限制", ge=1, le=1000),
    storage: MinIOClient = Depends(get_storage)
):
    """
    列出文件
    
    获取MinIO存储中的文件列表
    """
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Listing files with prefix: {prefix}")
        
        files = await storage.list_files(prefix=prefix, limit=limit)
        
        return {
            "success": True,
            "data": {
                "files": files,
                "count": len(files),
                "prefix": prefix,
                "limit": limit
            },
            "request_id": request_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except MinIOError as e:
        logger.warning(f"[{request_id}] MinIO error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error listing files")
        raise HTTPException(status_code=500, detail="获取文件列表失败")

@router.get("/health")
async def health_check(storage: MinIOClient = Depends(get_storage)):
    """健康检查接口"""
    # 检查MinIO存储状态
    storage_status = storage.health_check()
    
    return {
        "status": "healthy",
        "service": "images-api",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "storage": storage_status,
        "supported_models": [
            "gpt (gpt-image-1)",
            "recraft",
            "recraftv3",
            "seedream",
            "seededit",
            "flux",
            "cogview",
            "hunyuan",
            "kling",
            "stable-diffusion",
            "generic-images",
            "image-variations",
            "virtual-try-on",
            "flux-kontext",
            "hailuo",
            "doubao",
            "veo3 (official vertex ai video generation)"
        ],
        "file_storage": {
            "enabled": True,
            "endpoints": {
                "upload": f"{settings.api_prefix}/files/upload",
                "get_url": f"{settings.api_prefix}/files/{{object_name}}",
                "redirect": f"{settings.api_prefix}/files/{{object_name}}/redirect",
                "delete": f"{settings.api_prefix}/files/{{object_name}}",
                "list": f"{settings.api_prefix}/files"
            }
        }
    }

# =============================================================================
# 添加剩余的API端点
# =============================================================================

class StableDiffusionImageRequest(ImagesBaseRequest):
    """StableDiffusion图像创建请求"""
    prompt: str = Field(..., description="图像描述提示词")
    size: str = Field(default="1:1", description="图像尺寸比例", pattern="^(1:1|2:3|3:2|3:4|4:3|9:16|16:9)$")
    n: int = Field(default=1, description="生成图像数量", ge=1, le=10)

@router.post("/stable-diffusion/create", response_model=ImagesAPIResponse)
async def create_stable_diffusion_image(
    request: StableDiffusionImageRequest,
    service: ImagesService = Depends(get_service)
):
    """StableDiffusion图像创建接口"""
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Creating StableDiffusion image generation task")
        
        result = await service.create_stable_diffusion_image(
            prompt=request.prompt,
            size=request.size,
            n=request.n
        )
        
        return ImagesAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except ValueError as e:
        logger.warning(f"[{request_id}] Invalid request parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except ImagesAPIError as e:
        log_exception(logger, e, f"[{request_id}] Images API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

class GenericImageRequest(ImagesBaseRequest):
    """通用图像创建请求"""
    prompt: str = Field(..., description="图像描述提示词")
    model: str = Field(default="auto", description="模型名称")
    size: str = Field(default="1024x1024", description="图像尺寸")
    quality: str = Field(default="standard", description="图像质量")

@router.post("/images/create", response_model=ImagesAPIResponse)
async def create_generic_image(
    request: GenericImageRequest,
    service: ImagesService = Depends(get_service)
):
    """通用图像创建接口"""
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Creating generic image generation task")
        
        result = await service.create_generic_image(
            prompt=request.prompt,
            model=request.model,
            size=request.size,
            quality=request.quality
        )
        
        return ImagesAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except ValueError as e:
        logger.warning(f"[{request_id}] Invalid request parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except ImagesAPIError as e:
        log_exception(logger, e, f"[{request_id}] Images API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

class ImageVariationsRequest(ImagesBaseRequest):
    """图像变体创建请求"""
    image_url: str = Field(..., description="原始图像URL")
    n: int = Field(default=1, description="变体数量")
    size: str = Field(default="1024x1024", description="图像尺寸")

@router.post("/images/variations", response_model=ImagesAPIResponse)
async def create_image_variations(
    request: ImageVariationsRequest,
    service: ImagesService = Depends(get_service)
):
    """图像变体创建接口"""
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Creating image variations task")
        
        result = await service.create_image_variations(
            image_url=request.image_url,
            n=request.n,
            size=request.size
        )
        
        return ImagesAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except ValueError as e:
        logger.warning(f"[{request_id}] Invalid request parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except ImagesAPIError as e:
        log_exception(logger, e, f"[{request_id}] Images API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")


class FluxKontextImageRequest(ImagesBaseRequest):
    """flux-kontext图像生成请求"""
    prompt: str = Field(..., description="图像描述提示词")
    context_image: Optional[str] = Field(None, description="上下文图像URL")
    strength: float = Field(default=0.8, description="生成强度")
    seed: Optional[int] = Field(None, description="随机种子")

@router.post("/flux-kontext/generate", response_model=ImagesAPIResponse)
async def create_flux_kontext_image(
    request: FluxKontextImageRequest,
    service: ImagesService = Depends(get_service)
):
    """flux-kontext图像生成接口"""
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Creating flux-kontext image generation task")
        
        result = await service.create_flux_kontext_image(
            prompt=request.prompt,
            context_image=request.context_image,
            strength=request.strength,
            seed=request.seed
        )
        
        # 异步提交图片存储任务（KISS原则：在返回响应前异步提交）
        submit_image_storage_async(
            request_id=request_id,
            prompt=request.prompt,
            model="flux-kontext",
            result_data=result,
            generation_params={
                "context_image": request.context_image,
                "strength": request.strength,
                "seed": request.seed
            }
        )
        
        return ImagesAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except ValueError as e:
        logger.warning(f"[{request_id}] Invalid request parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except ImagesAPIError as e:
        log_exception(logger, e, f"[{request_id}] Images API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

class HailuoImageRequest(ImagesBaseRequest):
    """海螺图片生成请求"""
    prompt: str = Field(..., description="图像描述提示词")
    size: str = Field(default="1024x1024", description="图像尺寸")
    quality: str = Field(default="standard", description="图像质量")
    seed: Optional[int] = Field(None, description="随机种子")

@router.post("/hailuo/generate", response_model=ImagesAPIResponse)
async def create_hailuo_image(
    request: HailuoImageRequest,
    service: ImagesService = Depends(get_service)
):
    """海螺图片生成接口"""
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Creating Hailuo image generation task")
        
        result = await service.create_hailuo_image(
            prompt=request.prompt,
            size=request.size,
            quality=request.quality,
            seed=request.seed
        )
        
        # 异步提交图片存储任务（KISS原则：在返回响应前异步提交）
        submit_image_storage_async(
            request_id=request_id,
            prompt=request.prompt,
            model="hailuo",
            result_data=result,
            generation_params={
                "size": request.size,
                "quality": request.quality,
                "seed": request.seed
            }
        )
        
        return ImagesAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except ValueError as e:
        logger.warning(f"[{request_id}] Invalid request parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except ImagesAPIError as e:
        log_exception(logger, e, f"[{request_id}] Images API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

class DoubaoImageRequest(ImagesBaseRequest):
    """Doubao图片生成请求"""
    prompt: str = Field(..., description="图像描述提示词")
    size: str = Field(default="1024x1024", description="图像尺寸")
    guidance_scale: int = Field(default=3, description="指导强度")
    watermark: bool = Field(default=True, description="是否添加水印")

@router.post("/doubao/generate", response_model=ImagesAPIResponse)
async def create_doubao_image(
    request: DoubaoImageRequest,
    service: ImagesService = Depends(get_service)
):
    """Doubao图片生成接口"""
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Creating Doubao image generation task")
        
        result = await service.create_doubao_image(
            prompt=request.prompt,
            size=request.size,
            guidance_scale=request.guidance_scale,
            watermark=request.watermark
        )
        
        # 异步提交图片存储任务（KISS原则：在返回响应前异步提交）
        submit_image_storage_async(
            request_id=request_id,
            prompt=request.prompt,
            model="doubao",
            result_data=result,
            generation_params={
                "size": request.size,
                "guidance_scale": request.guidance_scale,
                "watermark": request.watermark
            }
        )
        
        return ImagesAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except ValueError as e:
        logger.warning(f"[{request_id}] Invalid request parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except ImagesAPIError as e:
        log_exception(logger, e, f"[{request_id}] Images API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")





# =============================================================================
# Google 官方 Veo3 视频生成接口
# =============================================================================



# =============================================================================
# Google官方Veo3 API接口
# =============================================================================

class Veo3OfficialRequest(BaseModel):
    """Google官方Veo3视频生成请求"""
    prompt: str = Field(..., description="视频生成提示词，详细描述想要生成的视频内容")
    duration: int = Field(default=5, description="视频时长(秒)，范围1-30")
    aspect_ratio: str = Field(default="16:9", description="宽高比，支持: 16:9, 9:16, 1:1, 4:3, 3:4")
    seed: Optional[int] = Field(None, description="随机种子，用于复现结果")
    guidance_scale: Optional[float] = Field(None, description="引导缩放值，控制生成与提示词的匹配程度")
    negative_prompt: Optional[str] = Field(None, description="负面提示词，描述不想要的内容")

@router.post("/veo3/official/generate", response_model=ImagesAPIResponse)
async def create_veo3_official_video(
    request: Veo3OfficialRequest,
    service: ImagesService = Depends(get_service)
):
    """
    Google官方Veo3视频生成接口
    
    使用Google官方Vertex AI Veo3 API异步生成视频
    """
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] 创建Google官方Veo3视频生成任务: {request.prompt[:50]}...")
        
        # 构建额外参数
        kwargs = {}
        if request.seed is not None:
            kwargs['seed'] = request.seed
        if request.guidance_scale is not None:
            kwargs['guidanceScale'] = request.guidance_scale
        if request.negative_prompt:
            kwargs['negativePrompt'] = request.negative_prompt
        
        result = await service.create_veo3_official_video(
            prompt=request.prompt,
            duration=request.duration,
            aspect_ratio=request.aspect_ratio,
            wait_for_completion=False,  # 强制异步模式
            max_wait=60,  # 设置默认值
            **kwargs
        )
        
        logger.info(f"[{request_id}] Google官方Veo3视频生成任务创建成功")
        
        # 如果任务创建成功，添加到队列供Celery处理
        if result.get('operation_id'):
            try:
                # 创建视频任务对象
                video_task = VideoTask(
                    task_id=request_id,
                    external_task_id=result['operation_id'],
                    prompt=request.prompt,
                    model="veo3-official",
                    status="pending",
                    metadata={
                        "duration": request.duration,
                        "aspect_ratio": request.aspect_ratio,
                        "seed": request.seed,
                        "guidance_scale": request.guidance_scale,
                        "negative_prompt": request.negative_prompt
                    }
                )
                
                # 添加到任务队列
                if simple_task_queue.add_task(video_task):
                    logger.info(f"[{request_id}] 任务已添加到队列，等待Celery处理")
                    
                    # 在响应中添加队列信息
                    result['queue_status'] = 'queued'
                    result['internal_task_id'] = request_id
                else:
                    logger.warning(f"[{request_id}] 任务添加到队列失败，但不影响主流程")
                    
            except Exception as queue_error:
                logger.warning(f"[{request_id}] 队列操作失败: {queue_error}，但不影响主流程")
        
        return ImagesAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except ValueError as e:
        logger.warning(f"[{request_id}] 请求参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except ImagesAPIError as e:
        log_exception(logger, e, f"[{request_id}] Google官方Veo3 API错误")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Google官方Veo3生成失败")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")

@router.get("/veo3/official/status/{operation_id:path}", response_model=ImagesAPIResponse)
async def get_veo3_official_status(
    operation_id: str,
    service: ImagesService = Depends(get_service)
):
    """
    查询Google官方Veo3任务状态
    
    查询Google Vertex AI Veo3长时间运行操作的状态
    """
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] 查询Google官方Veo3任务状态: {operation_id}")
        
        result = await service.check_veo3_official_status(operation_id)
        
        logger.info(f"[{request_id}] Google官方Veo3任务状态查询成功: {result.get('status', 'unknown')}")
        
        return ImagesAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except ValueError as e:
        logger.warning(f"[{request_id}] 操作ID格式错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except ImagesAPIError as e:
        log_exception(logger, e, f"[{request_id}] Google官方Veo3状态查询API错误")
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="任务不存在")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Google官方Veo3任务状态查询失败")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

