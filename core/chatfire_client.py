"""
ChatFire API网关客户端

专门处理ChatFire聚合的第三方模型
"""

from typing import Dict, Any, Optional, Union
from .base_client import BaseAPIClient, APIError

class ChatFireClient(BaseAPIClient):
    """ChatFire API网关专用客户端"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.chatfire.cc", timeout: int = 120):
        super().__init__(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout
        )
    
    async def generate_image(
        self,
        model: str,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """通过ChatFire网关生成图像"""
        data = {
            "model": model,
            "prompt": prompt
        }
        
        # 添加模型特定参数
        for key, value in kwargs.items():
            if value is not None:
                data[key] = value
        
        return await self._make_request("POST", "v1/images/generations", data)
    
    async def edit_image(
        self,
        model: str,
        image_url: str,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """通过ChatFire网关编辑图像"""
        data = {
            "model": model,
            "image_url": image_url,
            "prompt": prompt
        }
        
        # 添加其他参数
        for key, value in kwargs.items():
            if value is not None:
                data[key] = value
        
        return await self._make_request("POST", "v1/images/edits", data)
    
    async def generate_video(
        self,
        model: str,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """通过ChatFire网关生成视频"""
        data = {
            "model": model,
            "prompt": prompt
        }
        
        # 添加视频生成参数
        for key, value in kwargs.items():
            if value is not None:
                data[key] = value
        
        return await self._make_request("POST", "veo/v1/videos/generations", data)
    
    async def check_video_status(self, task_id: str) -> Dict[str, Any]:
        """检查视频生成状态"""
        params = {"id": task_id}
        return await self._make_request("GET", "veo/v1/videos/generations", params=params)