#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Images API 配置管理模块

集中管理应用的所有配置参数，包括:
- Images API配置
- 服务器配置
- FastMCP配置
- 高并发优化配置
"""

import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import Optional, Dict, Any

# 加载环境变量
load_dotenv()

class ImagesConfig(BaseModel):
    """Images API相关配置"""
    # API密钥配置
    api_key: str = Field(
        default="sk-idDBqyoDVqCXInnO9uaGLUfwsxY7RhzHSn166z5jOBCBvFmY",
        description="Images API密钥，服务器端统一配置"
    )
    # Google Gemini API配置
    gemini_api_key: str = Field(
        default=os.getenv("GEMINI_API_KEY", "AIzaSyDXn7uxY35vwHs3Ds9Z3dmJ9W2i4QBoLrc"),
        description="Google Gemini API密钥"
    )
    # Google Vertex AI配置
    vertex_project_id: str = Field(
        default=os.getenv("VERTEX_PROJECT_ID", ""),
        description="Google Cloud项目ID"
    )
    vertex_location: str = Field(
        default=os.getenv("VERTEX_LOCATION", "us-central1"),
        description="Vertex AI位置"
    )
    # Google Veo3配置
    veo3_project_id: str = Field(
        default=os.getenv("VEO3_PROJECT_ID", "qhhl-veo"),
        description="Google Veo3项目ID"
    )
    veo3_location: str = Field(
        default=os.getenv("VEO3_LOCATION", "us-central1"),
        description="Veo3服务位置"
    )
    google_credentials_path: str = Field(
        default=os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/Users/zac/workspace/google_oauth/qhhl-veo-26fd3f12ace3.json"),
        description="Google Cloud凭据文件路径"
    )
    veo3_storage_bucket: str = Field(
        default=os.getenv("VEO3_STORAGE_BUCKET", "veo-output-pub"),
        description="Veo3视频输出存储桶名称(需要是公开访问的)"
    )
    api_base_url: str = Field(
        default=os.getenv("IMAGES_API_BASE_URL", "https://api.chatfire.cc"),
        description="Images API基础URL"
    )
    request_timeout: int = Field(
        default=int(os.getenv("IMAGES_REQUEST_TIMEOUT", "120")),
        description="API请求超时时间(秒)"
    )
    max_retries: int = Field(
        default=int(os.getenv("IMAGES_MAX_RETRIES", "3")),
        description="API请求失败最大重试次数"
    )
    default_fields: Dict[str, str] = Field(
        default={
            "gpt": "prompt,model,n,size,quality,style",
            "recraft": "prompt,style,size,image_format",
            "seedream": "prompt,aspect_ratio,negative_prompt,cfg_scale,seed",
            "seededit": "image_url,prompt,strength,seed",
            "flux": "prompt,aspect_ratio,steps,guidance,seed",
            "recraftv3": "prompt,style,size,image_format",
            "cogview": "prompt,size,quality,seed",
            "hunyuan": "prompt,aspect_ratio,seed",
            "kling": "prompt,aspect_ratio,negative_prompt,cfg_scale,seed",
            "stable_diffusion": "prompt,negative_prompt,width,height,steps,guidance_scale,seed",
            "flux_kontext": "prompt,context_image,strength,seed",
            "hailuo": "prompt,size,quality,seed",
            "doubao": "prompt,size,quality,num_images,seed",
            "veo3": "prompt,duration,aspect_ratio,seed"
        },
        description="各功能默认参数字段列表"
    )

class ServerConfig(BaseModel):
    """服务器相关配置"""
    host: str = Field(
        default=os.getenv("HOST", "0.0.0.0"),
        description="服务器主机"
    )
    port: int = Field(
        default=int(os.getenv("PORT", "5512")),
        description="服务器端口"
    )
    debug: bool = Field(
        default=os.getenv("DEBUG", "False").lower() == "true",
        description="是否开启调试模式"
    )
    reload: bool = Field(
        default=os.getenv("RELOAD", "True").lower() == "true",
        description="是否开启热重载"
    )
    log_level: str = Field(
        default=os.getenv("LOG_LEVEL", "info"),
        description="日志级别"
    )
    # 高并发优化配置
    workers: int = Field(
        default=int(os.getenv("WORKERS", "4")),
        description="工作进程数量"
    )
    max_connections: int = Field(
        default=int(os.getenv("MAX_CONNECTIONS", "1000")),
        description="最大并发连接数"
    )
    keepalive_timeout: int = Field(
        default=int(os.getenv("KEEPALIVE_TIMEOUT", "30")),
        description="Keep-Alive超时时间"
    )
    timeout_keep_alive: int = Field(
        default=int(os.getenv("TIMEOUT_KEEP_ALIVE", "5")),
        description="保持连接超时"
    )
    # 服务器URL配置
    base_url: str = Field(
        default=os.getenv("SERVER_BASE_URL", "http://localhost:5512"),
        description="服务器基础URL，用于生成可访问的文件链接"
    )

class MCPConfig(BaseModel):
    """FastMCP相关配置"""
    host: str = Field(
        default=os.getenv("MCP_HOST", "0.0.0.0"),
        description="MCP服务器主机"
    )
    port: int = Field(
        default=int(os.getenv("MCP_PORT", "5513")),
        description="MCP服务器端口"
    )
    transport: str = Field(
        default=os.getenv("MCP_TRANSPORT", "streamable-http"),
        description="MCP传输方式 (stdio, streamable-http, sse)"
    )
    mount_path: str = Field(
        default=os.getenv("MCP_MOUNT_PATH", "/mcp"),
        description="在FastAPI中挂载的路径"
    )

class MinIOConfig(BaseModel):
    """MinIO对象存储配置"""
    endpoint: str = Field(
        default=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        description="MinIO服务端点"
    )
    access_key: str = Field(
        default=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        description="MinIO访问密钥"
    )
    secret_key: str = Field(
        default=os.getenv("MINIO_SECRET_KEY", "minioadmin123"),
        description="MinIO私钥"
    )
    secure: bool = Field(
        default=os.getenv("MINIO_SECURE", "False").lower() == "true",
        description="是否使用HTTPS"
    )
    bucket_name: str = Field(
        default=os.getenv("MINIO_BUCKET_NAME", "images"),
        description="默认存储桶名称"
    )
    region: str = Field(
        default=os.getenv("MINIO_REGION", "us-east-1"),
        description="存储区域"
    )
    url_expiry_hours: int = Field(
        default=int(os.getenv("MINIO_URL_EXPIRY_HOURS", "24")),
        description="生成的URL过期时间(小时)"
    )

class PerformanceConfig(BaseModel):
    """性能优化配置"""
    # HTTP连接池配置
    max_pool_connections: int = Field(
        default=int(os.getenv("MAX_POOL_CONNECTIONS", "100")),
        description="HTTP连接池最大连接数"
    )
    max_pool_connections_per_host: int = Field(
        default=int(os.getenv("MAX_POOL_CONNECTIONS_PER_HOST", "30")),
        description="每个主机的最大连接数"
    )
    dns_cache_ttl: int = Field(
        default=int(os.getenv("DNS_CACHE_TTL", "300")),
        description="DNS缓存TTL(秒)"
    )
    
    # 请求限流配置
    rate_limit_requests: int = Field(
        default=int(os.getenv("RATE_LIMIT_REQUESTS", "1000")),
        description="每分钟最大请求数"
    )
    rate_limit_burst: int = Field(
        default=int(os.getenv("RATE_LIMIT_BURST", "100")),
        description="突发请求限制"
    )
    
    # 超时配置
    connection_timeout: int = Field(
        default=int(os.getenv("CONNECTION_TIMEOUT", "10")),
        description="连接超时(秒)"
    )
    read_timeout: int = Field(
        default=int(os.getenv("READ_TIMEOUT", "30")),
        description="读取超时(秒)"
    )
    
    # 批量处理配置
    batch_size: int = Field(
        default=int(os.getenv("BATCH_SIZE", "50")),
        description="批量处理大小"
    )
    max_concurrent_requests: int = Field(
        default=int(os.getenv("MAX_CONCURRENT_REQUESTS", "100")),
        description="最大并发请求数"
    )

class Settings(BaseModel):
    """应用全局配置"""
    images: ImagesConfig = Field(default_factory=ImagesConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    minio: MinIOConfig = Field(default_factory=MinIOConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)

    # 其他配置项
    project_name: str = Field(
        default="Images API 代理服务",
        description="项目名称"
    )
    version: str = Field(
        default="1.0.0",
        description="应用版本"
    )
    api_prefix: str = Field(
        default="/api",
        description="API前缀"
    )

# 创建全局配置实例
settings = Settings()