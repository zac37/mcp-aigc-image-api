#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Kling API FastAPI 路由

提供 RESTful API 接口，兼容 OpenAI 风格的请求格式
"""

from fastapi import APIRouter, HTTPException, Header, Query, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
import uuid
from datetime import datetime

from services.kling_service import get_kling_service, KlingService
from core.kling_client import KlingAPIError
from core.logger import get_api_logger, log_exception
from core.config import settings

logger = get_api_logger()
router = APIRouter()

# =============================================================================
# 请求/响应模型
# =============================================================================

class KlingBaseRequest(BaseModel):
    """Kling API 基础请求模型"""
    pass

class TextToImageRequest(KlingBaseRequest):
    """文生图请求"""
    prompt: str = Field(..., description="文本描述，详细描述想要生成的图像内容")
    aspect_ratio: str = Field(default="1:1", description="宽高比，支持: 1:1, 16:9, 9:16, 4:3, 3:4")
    negative_prompt: Optional[str] = Field(None, description="负面提示词，描述不想要的内容")
    cfg_scale: float = Field(default=7.5, description="CFG缩放值，控制生成与提示词的匹配程度，范围1.0-20.0")
    seed: Optional[int] = Field(None, description="随机种子，用于复现结果")

class TextToVideoRequest(KlingBaseRequest):
    """文生视频请求"""
    prompt: str = Field(..., description="文本描述，详细描述想要生成的视频内容")
    aspect_ratio: str = Field(default="16:9", description="宽高比，支持: 16:9, 9:16, 1:1")
    duration: int = Field(default=5, description="视频时长（秒），支持: 5, 10")
    cfg_scale: float = Field(default=0.5, description="CFG缩放值，范围[0,1]")
    seed: Optional[int] = Field(None, description="随机种子")

class ImageToVideoRequest(KlingBaseRequest):
    """图生视频请求"""
    image_url: str = Field(..., description="输入图片的URL地址")
    prompt: Optional[str] = Field(None, description="可选的文本描述，用于指导视频生成")
    duration: int = Field(default=5, description="视频时长（秒），支持: 5, 10")
    cfg_scale: float = Field(default=0.5, description="CFG缩放值，范围[0,1]")
    seed: Optional[int] = Field(None, description="随机种子")

class VirtualTryOnRequest(KlingBaseRequest):
    """虚拟换衣请求"""
    person_image: str = Field(..., description="人物图片URL")
    garment_image: str = Field(..., description="服装图片URL")
    category: str = Field(default="tops", description="服装类别，支持: tops, bottoms, dresses, outerwear")

class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    progress: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    estimated_time: Optional[int] = None

class TaskResultResponse(BaseModel):
    """任务结果响应"""
    task_id: str
    status: str
    result_url: Optional[str] = None
    result_urls: Optional[List[str]] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None

class KlingAPIResponse(BaseModel):
    """Kling API 统一响应格式"""
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

# =============================================================================
# 依赖注入
# =============================================================================

def get_service() -> KlingService:
    """获取 Kling 服务实例"""
    return get_kling_service()

# =============================================================================
# API 路由
# =============================================================================

@router.post("/images/generations", response_model=KlingAPIResponse)
async def create_text_to_image(
    request: TextToImageRequest,
    service: KlingService = Depends(get_service)
):
    """
    文生图接口
    
    根据文本描述生成图像
    """
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Creating text-to-image task")
        
        result = await service.create_text_to_image_task(
            prompt=request.prompt,
            aspect_ratio=request.aspect_ratio,
            negative_prompt=request.negative_prompt,
            cfg_scale=request.cfg_scale,
            seed=request.seed
        )
        
        return KlingAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except ValueError as e:
        logger.warning(f"[{request_id}] Invalid request parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except KlingAPIError as e:
        log_exception(logger, e, f"[{request_id}] Kling API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/videos/text-to-video", response_model=KlingAPIResponse)
async def create_text_to_video(
    request: TextToVideoRequest,
    service: KlingService = Depends(get_service)
):
    """
    文生视频接口
    
    根据文本描述生成视频
    """
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Creating text-to-video task")
        
        result = await service.create_text_to_video_task(
            prompt=request.prompt,
            aspect_ratio=request.aspect_ratio,
            duration=request.duration,
            cfg_scale=request.cfg_scale,
            seed=request.seed
        )
        
        return KlingAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except ValueError as e:
        logger.warning(f"[{request_id}] Invalid request parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except KlingAPIError as e:
        log_exception(logger, e, f"[{request_id}] Kling API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/videos/image-to-video", response_model=KlingAPIResponse)
async def create_image_to_video(
    request: ImageToVideoRequest,
    service: KlingService = Depends(get_service)
):
    """
    图生视频接口
    
    根据输入图像和可选文本描述生成视频
    """
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Creating image-to-video task")
        
        result = await service.create_image_to_video_task(
            image_url=request.image_url,
            prompt=request.prompt,
            duration=request.duration,
            cfg_scale=request.cfg_scale,
            seed=request.seed
        )
        
        return KlingAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except ValueError as e:
        logger.warning(f"[{request_id}] Invalid request parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except KlingAPIError as e:
        log_exception(logger, e, f"[{request_id}] Kling API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/try-on/virtual", response_model=KlingAPIResponse)
async def create_virtual_try_on(
    request: VirtualTryOnRequest,
    service: KlingService = Depends(get_service)
):
    """
    虚拟换衣接口
    
    对人物图像进行虚拟换衣
    """
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Creating virtual try-on task")
        
        result = await service.create_virtual_try_on_task(
            person_image=request.person_image,
            garment_image=request.garment_image,
            category=request.category
        )
        
        return KlingAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except ValueError as e:
        logger.warning(f"[{request_id}] Invalid request parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except KlingAPIError as e:
        log_exception(logger, e, f"[{request_id}] Kling API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/tasks/{task_id}/status", response_model=KlingAPIResponse)
async def get_task_status(
    task_id: str,
    task_type: Optional[str] = Query(None, description="任务类型：text_to_image, text_to_video, image_to_video, virtual_try_on"),
    service: KlingService = Depends(get_service)
):
    """
    获取任务状态
    
    查询指定任务的当前状态和进度。
    支持指定任务类型以提高查询效率，如不指定则会自动尝试所有类型。
    """
    request_id = str(uuid.uuid4())
    
    try:
        logger.debug(f"[{request_id}] Getting status for task: {task_id}, type: {task_type}")
        
        result = await service.get_task_status(task_id=task_id, task_type=task_type)
        
        return KlingAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except KlingAPIError as e:
        log_exception(logger, e, f"[{request_id}] Kling API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/tasks/{task_id}/result", response_model=KlingAPIResponse)
async def get_task_result(
    task_id: str,
    service: KlingService = Depends(get_service)
):
    """
    获取任务结果
    
    获取已完成任务的结果文件URL
    """
    request_id = str(uuid.uuid4())
    
    try:
        logger.debug(f"[{request_id}] Getting result for task: {task_id}")
        
        result = await service.get_task_result(task_id=task_id)
        
        return KlingAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except KlingAPIError as e:
        log_exception(logger, e, f"[{request_id}] Kling API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/tasks/{task_id}", response_model=KlingAPIResponse)
async def get_single_task(
    task_id: str,
    task_type: Optional[str] = Query(None, description="任务类型：text_to_image, text_to_video, image_to_video, virtual_try_on"),
    service: KlingService = Depends(get_service)
):
    """
    获取单个任务完整信息
    
    获取任务的完整详细信息，包括状态、进度、结果等。
    支持指定任务类型以提高查询效率，如不指定则会自动尝试所有类型。
    """
    request_id = str(uuid.uuid4())
    
    try:
        logger.debug(f"[{request_id}] Getting complete info for task: {task_id}, type: {task_type}")
        
        result = await service.get_single_task(task_id=task_id, task_type=task_type)
        
        return KlingAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except KlingAPIError as e:
        log_exception(logger, e, f"[{request_id}] Kling API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/tasks/{task_id}/wait", response_model=KlingAPIResponse)
async def wait_for_task_completion(
    task_id: str,
    timeout: int = Query(default=300, description="超时时间（秒），最大600秒"),
    poll_interval: int = Query(default=5, description="轮询间隔（秒），最小1秒"),
    service: KlingService = Depends(get_service)
):
    """
    等待任务完成
    
    阻塞等待任务完成并返回最终结果，支持设置超时时间和轮询间隔
    """
    request_id = str(uuid.uuid4())
    
    # 参数验证
    if timeout > 600:
        raise HTTPException(status_code=400, detail="Timeout cannot exceed 600 seconds")
    if poll_interval < 1:
        raise HTTPException(status_code=400, detail="Poll interval must be at least 1 second")
    
    try:
        logger.info(f"[{request_id}] Waiting for task completion: {task_id}")
        
        result = await service.wait_for_task_completion(
            task_id=task_id,
            timeout=timeout,
            poll_interval=poll_interval
        )
        
        return KlingAPIResponse(
            success=True,
            data=result,
            request_id=request_id
        )
        
    except TimeoutError as e:
        logger.warning(f"[{request_id}] Task wait timeout: {e}")
        raise HTTPException(status_code=408, detail=str(e))
        
    except KlingAPIError as e:
        log_exception(logger, e, f"[{request_id}] Kling API error")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
        
    except Exception as e:
        log_exception(logger, e, f"[{request_id}] Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

# =============================================================================
# 健康检查
# =============================================================================

@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "kling-api",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }