"""
基础API客户端

提供HTTP请求、错误处理、重试等通用功能
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional, Union
from datetime import datetime
import time

from .logger import get_images_client_logger, log_exception, log_performance

logger = get_images_client_logger()


class APIError(Exception):
    """API异常基类"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)
    
    def __str__(self):
        return f"APIError({self.status_code}): {self.message}"


class BaseAPIClient:
    """基础API客户端类"""
    
    def __init__(self, base_url: str, api_key: str, timeout: int = 120):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建HTTP会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=self._get_default_headers()
            )
        return self._session
    
    def _get_default_headers(self) -> Dict[str, str]:
        """获取默认请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Images-API-Client/1.0"
        }
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """发送HTTP请求"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        session = await self._get_session()
        request_headers = self._get_default_headers()
        if headers:
            request_headers.update(headers)
        
        start_time = time.time()
        
        try:
            async with session.request(
                method,
                url,
                json=data,
                headers=request_headers,
                **kwargs
            ) as response:
                
                response_time = time.time() - start_time
                
                # 记录性能日志
                log_performance(
                    logger,
                    f"{method} {endpoint}",
                    response_time,
                    response.status
                )
                
                response_data = await response.json()
                
                if response.status >= 400:
                    raise APIError(
                        message=response_data.get('error', {}).get('message', str(response_data)),
                        status_code=response.status,
                        error_code=response_data.get('error', {}).get('code')
                    )
                
                return response_data
                
        except aiohttp.ClientError as e:
            log_exception(logger, e, f"HTTP request failed: {method} {url}")
            raise APIError(f"Network error: {str(e)}")
        except asyncio.TimeoutError:
            raise APIError(f"Request timeout after {self.timeout}s")
        except json.JSONDecodeError:
            raise APIError("Invalid JSON response")
    
    async def _make_multipart_request(
        self,
        method: str,
        endpoint: str,
        files: Optional[Dict[str, Union[str, bytes]]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """发送multipart请求（用于文件上传）"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        session = await self._get_session()
        request_headers = {"Authorization": f"Bearer {self.api_key}"}
        if headers:
            request_headers.update(headers)
        
        # 构建FormData
        form_data = aiohttp.FormData()
        if data:
            for key, value in data.items():
                form_data.add_field(key, str(value))
        
        if files:
            for key, file_content in files.items():
                if isinstance(file_content, bytes):
                    form_data.add_field(key, file_content, filename=f"{key}.bin")
                else:
                    form_data.add_field(key, file_content)
        
        try:
            async with session.request(
                method,
                url,
                data=form_data,
                headers=request_headers
            ) as response:
                
                response_data = await response.json()
                
                if response.status >= 400:
                    raise APIError(
                        message=response_data.get('error', {}).get('message', str(response_data)),
                        status_code=response.status
                    )
                
                return response_data
                
        except aiohttp.ClientError as e:
            log_exception(logger, e, f"Multipart request failed: {method} {url}")
            raise APIError(f"Network error: {str(e)}")
    
    async def close(self):
        """关闭客户端连接"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug(f"{self.__class__.__name__} session closed")