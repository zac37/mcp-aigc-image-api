"""
Google Vertex AI客户端

专门处理Google Vertex AI Veo3视频生成
"""

import json
import os
from typing import Dict, Any, Optional, Tuple
from google.auth import default
from google.auth.transport.requests import Request

from .base_client import BaseAPIClient, APIError
from .simple_config import settings
from .logger import get_api_logger

logger = get_api_logger()


class VertexAIClient:
    """Google Vertex AI专用客户端"""
    
    def __init__(self, project_id: str, location: str = "us-central1", credentials_path: Optional[str] = None):
        self.project_id = project_id
        self.location = location
        self.credentials_path = credentials_path
        self.credentials = None
        self.base_url = f"https://{location}-aiplatform.googleapis.com/v1"
        self.model_id = "veo-3.0-generate-preview"
        
        # 设置环境变量
        if credentials_path and os.path.exists(credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        logger.info(f"初始化VertexAI客户端 - 项目: {project_id}, 位置: {location}")
    
    def _get_credentials(self):
        """获取并初始化凭据对象"""
        if self.credentials is None:
            try:
                if self.credentials_path and not os.path.exists(self.credentials_path):
                    raise APIError(f"凭据文件不存在: {self.credentials_path}")
                
                # 获取默认凭据
                self.credentials, _ = default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
                logger.info(f"凭据初始化成功 - 项目: {self.project_id}")
                
            except Exception as e:
                logger.error(f"凭据初始化失败: {e}")
                raise APIError(f"凭据初始化失败: {e}")
        
        return self.credentials
    
    def _get_access_token(self) -> str:
        """获取访问令牌，自动处理令牌刷新"""
        credentials = self._get_credentials()
        
        # 检查令牌是否过期，如果过期则刷新
        if credentials.expired or not credentials.token:
            try:
                auth_req = Request()
                credentials.refresh(auth_req)
                logger.info("访问令牌已刷新")
            except Exception as e:
                logger.error(f"令牌刷新失败: {e}")
                raise APIError(f"令牌刷新失败: {e}")
        
        return credentials.token
    
    async def generate_video(
        self,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        seed: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        negative_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        异步生成视频
        
        Returns:
            operation_id: 任务操作ID
        """
        try:
            access_token = self._get_access_token()
            
            url = (f"{self.base_url}/projects/{self.project_id}/locations/{self.location}/"
                  f"publishers/google/models/{self.model_id}:predictLongRunning")
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json; charset=utf-8'
            }
            
            # 构建请求参数
            parameters = {
                "prompt": prompt,
                "duration": f"{duration}s",
                "aspectRatio": aspect_ratio
            }
            
            if seed is not None:
                parameters["seed"] = seed
            if guidance_scale is not None:
                parameters["guidanceScale"] = guidance_scale
            if negative_prompt:
                parameters["negativePrompt"] = negative_prompt
            
            payload = {
                "instances": [{"parameters": parameters}]
            }
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        operation_id = result.get('name')
                        logger.info(f"Veo3异步任务已提交 - ID: {operation_id}")
                        return operation_id
                    else:
                        error_text = await response.text()
                        logger.error(f"Veo3 API调用失败: {response.status} - {error_text}")
                        raise APIError(f"API调用失败: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Veo3视频生成失败: {e}")
            raise APIError(f"视频生成失败: {e}")
    
    async def check_status(self, operation_id: str) -> Dict[str, Any]:
        """检查任务状态"""
        try:
            access_token = self._get_access_token()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(operation_id, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise APIError(f"状态查询失败: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"状态查询失败: {e}")
            raise APIError(f"状态查询失败: {e}")