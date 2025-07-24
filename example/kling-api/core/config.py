#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Kling API 配置管理模块

集中管理应用的所有配置参数，包括:
- Kling API配置
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

class KlingConfig(BaseModel):
    """Kling API相关配置"""
    # API密钥配置
    api_key: str = Field(
        default="sk-idDBqyoDVqCXInnO9uaGLUfwsxY7RhzHSn166z5jOBCBvFmY",
        description="Kling API密钥，服务器端统一配置"
    )
    api_base_url: str = Field(
        default=os.getenv("KLING_API_BASE_URL", "https://api.chatfire.cn"),
        description="Kling API基础URL"
    )
    request_timeout: int = Field(
        default=int(os.getenv("KLING_REQUEST_TIMEOUT", "30")),
        description="API请求超时时间(秒)"
    )
    max_retries: int = Field(
        default=int(os.getenv("KLING_MAX_RETRIES", "3")),
        description="API请求失败最大重试次数"
    )
    default_fields: Dict[str, str] = Field(
        default={
            "text_to_image": "prompt,aspect_ratio,negative_prompt,cfg_scale,seed",
            "text_to_video": "prompt,aspect_ratio,duration,cfg_scale,seed",
            "image_to_video": "image_url,prompt,duration,cfg_scale,seed",
            "virtual_try_on": "person_image,garment_image,category",
            "task_status": "task_id,status,progress,created_at,updated_at",
            "task_result": "task_id,status,result_url,error_message"
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
        default=int(os.getenv("PORT", "5511")),
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

class MCPConfig(BaseModel):
    """FastMCP相关配置"""
    host: str = Field(
        default=os.getenv("MCP_HOST", "0.0.0.0"),
        description="MCP服务器主机"
    )
    port: int = Field(
        default=int(os.getenv("MCP_PORT", "5510")),
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
    kling: KlingConfig = Field(default_factory=KlingConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)

    # 其他配置项
    project_name: str = Field(
        default="Kling API 代理服务",
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