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

logger = get_api_logger()
router = APIRouter()

# =============================================================================
# 请求/响应模型
# =============================================================================

class ImagesBaseRequest(BaseModel):
    """Images API 基础请求模型"""
    pass

class GPTImageRequest(ImagesBaseRequest):
    """GPT图像生成请求"""
    prompt: str = Field(..., description="图像描述提示词，详细描述想要生成的图像内容")
    model: str = Field(default="dall-e-3", description="模型名称，支持: dall-e-3, dall-e-2")
    n: int = Field(default=1, description="生成图像数量，dall-e-3最多1张，dall-e-2最多10张")
    size: str = Field(default="1024x1024", description="图像尺寸，支持多种规格")
    quality: str = Field(default="standard", description="图像质量，支持: standard, hd")
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
        
        result = await service.create_gpt_image(
            prompt=request.prompt,
            model=request.model,
            n=request.n,
            size=request.size,
            quality=request.quality,
            style=request.style
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
            "gpt (dall-e-2, dall-e-3)",
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
            "kolors",
            "virtual-try-on",
            "flux-kontext",
            "hailuo",
            "doubao"
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

class KolorsImageRequest(ImagesBaseRequest):
    """Kolors图像生成请求"""
    prompt: str = Field(..., description="图像描述提示词")
    image_url: Optional[str] = Field(None, description="输入图像URL（img2img模式）")
    mode: str = Field(default="text2img", description="生成模式")
    strength: float = Field(default=0.8, description="生成强度")
    seed: Optional[int] = Field(None, description="随机种子")

@router.post("/kolors/generate", response_model=ImagesAPIResponse)
async def create_kolors_image(
    request: KolorsImageRequest,
    service: ImagesService = Depends(get_service)
):
    """Kolors图像生成接口"""
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Creating Kolors image generation task")
        
        result = await service.create_kolors_image(
            prompt=request.prompt,
            image_url=request.image_url,
            mode=request.mode,
            strength=request.strength,
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