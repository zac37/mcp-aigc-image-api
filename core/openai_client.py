"""
OpenAI API客户端

专门处理OpenAI GPT/DALL-E系列模型
"""

from typing import Dict, Any, Optional, Union
from .base_client import BaseAPIClient, APIError

class OpenAIClient(BaseAPIClient):
    """OpenAI API专用客户端"""
    
    def __init__(self, api_key: str, timeout: int = 120):
        super().__init__(
            base_url="https://api.openai.com",
            api_key=api_key,
            timeout=timeout
        )
    
    async def generate_image(
        self,
        prompt: str,
        model: str = "gpt-image-1",
        n: int = 1,
        size: str = "1024x1024",
        quality: str = "auto",
        background: str = "auto",
        moderation: str = "auto",
        **kwargs
    ) -> Dict[str, Any]:
        """GPT图像生成"""
        data = {
            "model": model,
            "prompt": prompt,
            "n": n,
            "size": size,
            "quality": quality,
            "background": background,
            "moderation": moderation
        }
        
        # 添加其他可选参数
        for key, value in kwargs.items():
            if value is not None:
                data[key] = value
        
        return await self._make_request("POST", "v1/images/generations", data)
    
    async def edit_image(
        self,
        image_content: bytes,
        prompt: str,
        model: str = "gpt-image-1",
        mask_content: Optional[bytes] = None,
        n: int = 1,
        size: str = "1024x1024"
    ) -> Dict[str, Any]:
        """GPT图像编辑"""
        files = {"image": image_content}
        if mask_content:
            files["mask"] = mask_content
        
        data = {
            "prompt": prompt,
            "model": model,
            "n": n,
            "size": size
        }
        
        return await self._make_multipart_request("POST", "v1/images/edits", files, data)