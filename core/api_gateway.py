"""
Images API智能路由网关

统一管理三个API提供方，实现智能路由
"""

from typing import Dict, Any, Optional, Union
from .openai_client import OpenAIClient
from .vertex_client import VertexAIClient  
from .chatfire_client import ChatFireClient
from .base_client import APIError
from .logger import get_api_logger

logger = get_api_logger()


class ImageAPIGateway:
    """Images API智能路由网关"""
    
    # 模型路由映射表 - 简单清晰的路由逻辑
    MODEL_ROUTES = {
        # OpenAI直连模型
        "gpt-image-1": "openai",
        "dall-e-2": "openai", 
        "dall-e-3": "openai",
        
        # Google Vertex AI直连模型
        "veo3-official": "vertex",
        "veo-3.0-generate-preview": "vertex",
        
        # 其他所有模型通过ChatFire网关
        # (recraft, flux, seedream, stable-diffusion等)
    }
    
    def __init__(
        self,
        chatfire_api_key: str,
        openai_api_key: Optional[str] = None,
        vertex_project_id: Optional[str] = None,
        vertex_location: str = "us-central1",
        vertex_credentials_path: Optional[str] = None,
        chatfire_base_url: str = "https://api.chatfire.cc"
    ):
        """初始化API网关"""
        
        # ChatFire客户端 (必需，处理大部分第三方模型)
        self.chatfire = ChatFireClient(
            api_key=chatfire_api_key,
            base_url=chatfire_base_url
        )
        
        # OpenAI客户端 (可选，处理GPT系列)
        self.openai = None
        if openai_api_key:
            self.openai = OpenAIClient(api_key=openai_api_key)
        
        # Vertex AI客户端 (可选，处理Veo3系列)
        self.vertex = None
        if vertex_project_id:
            self.vertex = VertexAIClient(
                project_id=vertex_project_id,
                location=vertex_location,
                credentials_path=vertex_credentials_path
            )
        
        logger.info("API网关初始化完成")
    
    def _get_provider(self, model: str) -> str:
        """根据模型名确定API提供方"""
        return self.MODEL_ROUTES.get(model, "chatfire")
    
    def _get_client(self, provider: str):
        """获取对应的客户端"""
        if provider == "openai":
            if not self.openai:
                raise APIError("OpenAI客户端未配置")
            return self.openai
        elif provider == "vertex":
            if not self.vertex:
                raise APIError("Vertex AI客户端未配置")
            return self.vertex
        elif provider == "chatfire":
            return self.chatfire
        else:
            raise APIError(f"未知的API提供方: {provider}")
    
    async def generate_image(
        self,
        model: str,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """统一图像生成接口"""
        provider = self._get_provider(model)
        client = self._get_client(provider)
        
        logger.info(f"路由图像生成请求: {model} -> {provider}")
        
        try:
            if provider == "openai":
                # OpenAI特殊处理
                return await client.generate_image(prompt=prompt, model=model, **kwargs)
            elif provider == "vertex":
                # Vertex AI不支持图像生成，抛出错误
                raise APIError("Vertex AI客户端不支持图像生成，请使用视频生成")
            else:
                # ChatFire网关处理
                return await client.generate_image(model=model, prompt=prompt, **kwargs)
                
        except Exception as e:
            logger.error(f"图像生成失败: {model} -> {provider} - {e}")
            raise
    
    async def edit_image(
        self,
        model: str,
        image_content: Optional[bytes] = None,
        image_url: Optional[str] = None,
        prompt: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """统一图像编辑接口"""
        provider = self._get_provider(model)
        client = self._get_client(provider)
        
        logger.info(f"路由图像编辑请求: {model} -> {provider}")
        
        try:
            if provider == "openai":
                if not image_content:
                    raise APIError("OpenAI图像编辑需要提供image_content")
                return await client.edit_image(
                    image_content=image_content,
                    prompt=prompt,
                    model=model,
                    **kwargs
                )
            else:
                # ChatFire网关处理
                if not image_url:
                    raise APIError("ChatFire图像编辑需要提供image_url")
                return await client.edit_image(
                    model=model,
                    image_url=image_url,
                    prompt=prompt,
                    **kwargs
                )
                
        except Exception as e:
            logger.error(f"图像编辑失败: {model} -> {provider} - {e}")
            raise
    
    async def generate_video(
        self,
        model: str,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """统一视频生成接口"""
        provider = self._get_provider(model)
        client = self._get_client(provider)
        
        logger.info(f"路由视频生成请求: {model} -> {provider}")
        
        try:
            if provider == "vertex":
                # Vertex AI返回operation_id
                operation_id = await client.generate_video(prompt=prompt, **kwargs)
                return {
                    "operation_id": operation_id,
                    "status": "submitted",
                    "provider": "vertex"
                }
            else:
                # ChatFire网关处理
                return await client.generate_video(model=model, prompt=prompt, **kwargs)
                
        except Exception as e:
            logger.error(f"视频生成失败: {model} -> {provider} - {e}")
            raise
    
    async def check_video_status(self, model: str, task_id: str) -> Dict[str, Any]:
        """检查视频任务状态"""
        provider = self._get_provider(model)
        client = self._get_client(provider)
        
        try:
            if provider == "vertex":
                return await client.check_status(operation_id=task_id)
            else:
                return await client.check_video_status(task_id=task_id)
                
        except Exception as e:
            logger.error(f"状态查询失败: {model} -> {provider} - {e}")
            raise
    
    async def close(self):
        """关闭所有客户端连接"""
        if self.openai:
            await self.openai.close()
        if self.chatfire:
            await self.chatfire.close()
        # Vertex AI客户端不需要关闭
        logger.info("API网关已关闭")


# 全局网关实例
_gateway_instance: Optional[ImageAPIGateway] = None


def get_api_gateway() -> ImageAPIGateway:
    """获取全局API网关实例"""
    global _gateway_instance
    if _gateway_instance is None:
        from .simple_config import settings
        _gateway_instance = ImageAPIGateway(
            chatfire_api_key=settings.api_key,
            openai_api_key=getattr(settings, 'openai_api_key', None),
            vertex_project_id=getattr(settings, 'vertex_project_id', None),
            vertex_location=getattr(settings, 'vertex_location', 'us-central1'),
            vertex_credentials_path=getattr(settings, 'google_credentials_path', None),
            chatfire_base_url=getattr(settings, 'api_base_url', 'https://api.chatfire.cc')
        )
    return _gateway_instance


async def cleanup_api_gateway():
    """清理全局API网关"""
    global _gateway_instance
    if _gateway_instance:
        await _gateway_instance.close()
        _gateway_instance = None