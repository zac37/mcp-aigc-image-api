#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Images API 主应用程序

提供 FastAPI 和 MCP 双协议支持的图像生成 AI 服务
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn
import logging
from contextlib import asynccontextmanager

from routers import api
from core.simple_config import compat_settings as settings
from core.logger import get_main_logger
from core.compatibility_adapter import cleanup_images_client
from core.minio_client import cleanup_minio_client

# 创建日志记录器
logger = get_main_logger()

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("Starting Images API service...")
    logger.info(f"Service will run on {settings.server.host}:{settings.server.port}")
    logger.info(f"MCP service will run on {settings.mcp.mcp_host}:{settings.mcp.mcp_port}")
    
    yield
    
    # 关闭时执行
    logger.info("Shutting down Images API service...")
    
    await cleanup_images_client()
    await cleanup_minio_client()
    logger.info("Cleanup completed")



# 创建 FastAPI 应用
app = FastAPI(
    title=settings.project_name,
    description="""
    通过FastAPI封装多种图像生成AI API，提供两种风格接口:
    
    1. 原生API风格 (/api/...): 保持与各API相同的参数和响应结构
    2. MCP风格: 支持FastMCP 2.5标准接口，提供streamable-http协议
    
    主要功能:
    - GPT图像生成: 根据文本描述生成高质量图像
    - Recraft图像生成: 专业的图像创作工具
    - 即梦3.0(Seedream): 先进的图像生成技术
    - 即梦垫图(SeedEdit): 图像编辑和优化
    - FLUX图像创建: 高质量的图像生成
    - Recraftv3图像创建: 最新版本的图像生成
    - Cogview图像创建: 清华大学的图像生成模型
    - 混元图像创建: 腾讯的图像生成技术
    - Kling图像创建: 快手的图像生成服务
    - StableDiffusion: 开源的图像生成模型
    - Kolors: 多彩图像生成
    - 虚拟换衣: AI驱动的虚拟试衣功能
    - flux-kontext: 上下文感知的图像生成
    - 海螺图片: 海螺AI的图像生成
    - Doubao图片生成: 字节跳动的图像生成
    
    支持的协议:
    - REST API (FastAPI)
    - MCP (Model Context Protocol) via streamable-http
    
    鉴权方式:
    - Header: Authorization: Bearer <your-api-key>
    """,
    version=settings.version,
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加请求日志中间件（临时禁用以解决权限问题）
# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     """请求日志中间件"""
#     import time
#     from core.logger import get_access_logger
#     
#     access_logger = get_access_logger()
#     start_time = time.time()
#     
#     # 记录请求
#     client_ip = request.client.host if request.client else "unknown"
#     user_agent = request.headers.get("user-agent", "unknown")
#     
#     response = await call_next(request)
#     
#     # 计算处理时间
#     process_time = time.time() - start_time
#     
#     # 记录访问日志
#     access_logger.info(
#         f"{client_ip} - \"{request.method} {request.url.path}\" "
#         f"{response.status_code} - {process_time:.3f}s - \"{user_agent}\""
#     )
#     
#     return response

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    from core.logger import log_exception
    
    log_exception(logger, exc, f"Unhandled exception in {request.method} {request.url.path}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "path": str(request.url.path),
            "method": request.method
        }
    )

# 挂载路由
app.include_router(api.router, prefix=settings.api_prefix, tags=["Images API"])

# 根路径
@app.get("/")
async def root():
    """根路径信息"""
    return {
        "service": "Images API",
        "version": settings.version,
        "description": "多种图像生成AI API代理服务，支持GPT、Recraft、FLUX、Stable Diffusion等多种模型",
        "docs": "/docs",
        "api_prefix": settings.api_prefix,
        "mcp": {
            "enabled": True,
            "host": settings.mcp.mcp_host,
            "port": settings.mcp.mcp_port,
            "transport": settings.mcp.mcp_transport
        },
        "supported_models": [
            "gpt",
            "recraft",
            "seedream",
            "seededit", 
            "flux",
            "recraftv3",
            "cogview",
            "hunyuan",
            "kling",
            "stable-diffusion",
            "kolors",
            "virtual-try-on",
            "flux-kontext",
            "hailuo",
            "doubao"
        ],
        "endpoints": {
            "gpt_generations": "/api/gpt/generations",
            "recraft_generate": "/api/recraft/generate",
            "seedream_generate": "/api/seedream/generate",
            "seededit_generate": "/api/seededit/generate",
            "flux_create": "/api/flux/create",
            "recraftv3_create": "/api/recraftv3/create",
            "cogview_create": "/api/cogview/create",
            "hunyuan_create": "/api/hunyuan/create",
            "kling_create": "/api/kling/create",
            "stable_diffusion_create": "/api/stable-diffusion/create",
            "kolors_generate": "/api/kolors/generate",
            "flux_kontext_generate": "/api/flux-kontext/generate",
            "hailuo_generate": "/api/hailuo/generate",
            "doubao_generate": "/api/doubao/generate",
            "file_upload": "/api/files/upload",
            "file_access": "/api/files/{object_name}",
            "file_redirect": "/api/files/{object_name}/redirect",
            "file_delete": "/api/files/{object_name}",
            "file_list": "/api/files"
        },
        "file_storage": {
            "enabled": True,
            "minio_endpoint": settings.minio.minio_endpoint,
            "default_bucket": settings.minio.minio_bucket,
            "supported_formats": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"],
            "max_file_size_mb": 50
        }
    }

# MCP服务需要独立运行，不再挂载到FastAPI
# 这与 kling-api 的架构保持一致

if __name__ == "__main__":
    # 开发环境直接运行
    uvicorn.run(
        "main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.debug,
        log_level=settings.server.log_level.lower(),
        access_log=False,  # 使用自定义访问日志
    )