"""
简化的配置管理 - 遵循KISS原则

将原来7个配置类合并为1个核心配置类
"""

import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import Optional

# 加载环境变量
load_dotenv()


class AppSettings(BaseModel):
    """应用核心配置 - 遵循最小必要原则"""
    
    # ===============================================
    # 基础服务配置
    # ===============================================
    project_name: str = Field(
        default="Images API",
        description="项目名称"
    )
    version: str = Field(
        default="1.0.0", 
        description="版本号"
    )
    host: str = Field(
        default="0.0.0.0",
        description="服务绑定地址"
    )
    port: int = Field(
        default=5512,
        description="服务端口"
    )
    
    # ===============================================
    # API密钥配置 (三个关键配置)
    # ===============================================
    api_key: str = Field(
        default=os.getenv("IMAGES_API_KEY", "sk-idDBqyoDVqCXInnO9uaGLUfwsxY7RhzHSn166z5jOBCBvFmY"),
        description="ChatFire API密钥"
    )
    openai_api_key: Optional[str] = Field(
        default=os.getenv("OPENAI_API_KEY"),
        description="OpenAI API密钥 (可选)"
    )
    google_credentials_path: Optional[str] = Field(
        default=os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/Users/zac/workspace/google_oauth/qhhl-veo-26fd3f12ace3.json"),
        description="Google Cloud凭据文件路径 (可选)"
    )
    
    # ===============================================
    # API基础URL配置
    # ===============================================
    api_base_url: str = Field(
        default=os.getenv("IMAGES_API_BASE_URL", "https://api.chatfire.cc"),
        description="ChatFire API基础URL"
    )
    
    # ===============================================
    # Google Vertex AI配置 (仅Veo3需要)
    # ===============================================
    vertex_project_id: Optional[str] = Field(
        default=os.getenv("VERTEX_PROJECT_ID", "qhhl-veo"),
        description="Google Cloud项目ID"
    )
    vertex_location: str = Field(
        default=os.getenv("VERTEX_LOCATION", "us-central1"),
        description="Vertex AI位置"
    )
    veo3_project_id: Optional[str] = Field(
        default=os.getenv("VEO3_PROJECT_ID", "qhhl-veo"),
        description="Veo3项目ID"
    )
    veo3_location: str = Field(
        default=os.getenv("VEO3_LOCATION", "us-central1"),
        description="Veo3位置"
    )
    veo3_storage_bucket: Optional[str] = Field(
        default=os.getenv("VEO3_STORAGE_BUCKET", ""),
        description="Veo3存储桶 (可选)"
    )
    
    # ===============================================
    # 存储配置
    # ===============================================
    redis_url: str = Field(
        default=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        description="Redis连接URL"
    )
    redis_host: str = Field(
        default=os.getenv("REDIS_HOST", "localhost"),
        description="Redis主机"
    )
    redis_port: int = Field(
        default=int(os.getenv("REDIS_PORT", "6379")),
        description="Redis端口"
    )
    redis_password: Optional[str] = Field(
        default=os.getenv("REDIS_PASSWORD"),
        description="Redis密码"
    )
    redis_db: int = Field(
        default=int(os.getenv("REDIS_DB", "0")),
        description="Redis数据库"
    )
    
    minio_endpoint: str = Field(
        default=os.getenv("MINIO_ENDPOINT", "172.22.0.3:9000"),
        description="MinIO存储端点"
    )
    minio_access_key: str = Field(
        default=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        description="MinIO访问密钥"
    )
    minio_secret_key: str = Field(
        default=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        description="MinIO秘密密钥"
    )
    minio_bucket: str = Field(
        default=os.getenv("MINIO_BUCKET", "images"),
        description="MinIO默认存储桶"
    )
    minio_secure: bool = Field(
        default=os.getenv("MINIO_SECURE", "false").lower() == "true",
        description="MinIO使用SSL"
    )
    minio_region: str = Field(
        default=os.getenv("MINIO_REGION", "us-east-1"),
        description="MinIO区域"
    )
    minio_url_expiry_hours: int = Field(
        default=int(os.getenv("MINIO_URL_EXPIRY_HOURS", "24")),
        description="MinIO URL过期时间(小时)"
    )
    
    # ===============================================
    # 性能配置 (简化版)
    # ===============================================
    request_timeout: int = Field(
        default=int(os.getenv("REQUEST_TIMEOUT", "120")),
        description="API请求超时时间(秒)"
    )
    max_retries: int = Field(
        default=int(os.getenv("MAX_RETRIES", "3")),
        description="最大重试次数"
    )
    
    # ===============================================
    # JARVIS集成配置
    # ===============================================
    jarvis_enabled: bool = Field(
        default=os.getenv("JARVIS_ENABLED", "false").lower() == "true",
        description="启用JARVIS集成"
    )
    jarvis_api_base_url: str = Field(
        default=os.getenv("JARVIS_API_BASE_URL", "http://localhost:8000"),
        description="JARVIS API基础URL"
    )
    jarvis_callback_endpoint: str = Field(
        default=os.getenv("JARVIS_CALLBACK_ENDPOINT", "/api/materials/notify"),
        description="JARVIS回调端点"
    )
    jarvis_api_key: Optional[str] = Field(
        default=os.getenv("JARVIS_API_KEY"),
        description="JARVIS API密钥 (可选)"
    )
    jarvis_default_product_id: int = Field(
        default=int(os.getenv("JARVIS_DEFAULT_PRODUCT_ID", "1")),
        description="JARVIS默认产品ID"
    )
    jarvis_default_tag_id: int = Field(
        default=int(os.getenv("JARVIS_DEFAULT_TAG_ID", "1")),
        description="JARVIS默认标签ID"
    )
    jarvis_retry_count: int = Field(
        default=int(os.getenv("JARVIS_RETRY_COUNT", "3")),
        description="JARVIS重试次数"
    )
    jarvis_retry_delay: int = Field(
        default=int(os.getenv("JARVIS_RETRY_DELAY", "2")),
        description="JARVIS重试延迟(秒)"
    )
    jarvis_timeout: int = Field(
        default=int(os.getenv("JARVIS_TIMEOUT", "30")),
        description="JARVIS请求超时(秒)"
    )
    
    # ===============================================
    # 服务器配置
    # ===============================================
    server_host: str = Field(
        default=os.getenv("SERVER_HOST", "0.0.0.0"),
        description="服务器绑定地址"
    )
    server_port: int = Field(
        default=int(os.getenv("SERVER_PORT", "5512")),
        description="服务器端口"
    )
    server_base_url: str = Field(
        default=os.getenv("SERVER_BASE_URL", "http://localhost:5512"),
        description="服务器基础URL"
    )
    api_prefix: str = Field(
        default=os.getenv("API_PREFIX", "/api"),
        description="API前缀"
    )
    
    # ===============================================
    # MCP服务配置
    # ===============================================
    mcp_host: str = Field(
        default=os.getenv("MCP_HOST", "0.0.0.0"),
        description="MCP服务主机"
    )
    mcp_port: int = Field(
        default=int(os.getenv("MCP_PORT", "5513")),
        description="MCP服务端口"
    )
    mcp_transport: str = Field(
        default=os.getenv("MCP_TRANSPORT", "streamable-http"),
        description="MCP传输协议"
    )
    
    # ===============================================
    # 开发调试配置
    # ===============================================
    debug: bool = Field(
        default=os.getenv("DEBUG", "false").lower() == "true",
        description="调试模式"
    )
    log_level: str = Field(
        default=os.getenv("LOG_LEVEL", "INFO"),
        description="日志级别"
    )
    
    class Config:
        """Pydantic配置"""
        # 允许环境变量覆盖
        case_sensitive = False
        # 启用任意类型
        arbitrary_types_allowed = True


# 全局配置实例
settings = AppSettings()


# 为了兼容性，提供一些别名
class CompatibilitySettings:
    """兼容性设置，提供原有配置的访问方式"""
    
    def __init__(self, settings: AppSettings):
        self._settings = settings
    
    @property
    def images(self):
        """兼容原有的images配置访问"""
        return self._settings
    
    @property
    def server(self):
        """兼容原有的server配置访问"""
        return self._settings
    
    @property
    def minio(self):
        """兼容原有的minio配置访问"""
        return self._settings
    
    @property
    def mcp(self):
        """兼容原有的mcp配置访问"""
        return self._settings
    
    @property
    def redis(self):
        """兼容原有的redis配置访问"""
        return self._settings
    
    @property
    def project_name(self):
        return self._settings.project_name
    
    @property
    def version(self):
        return self._settings.version
    
    @property
    def api_prefix(self):
        return "/api"


# 兼容性实例
compat_settings = CompatibilitySettings(settings)