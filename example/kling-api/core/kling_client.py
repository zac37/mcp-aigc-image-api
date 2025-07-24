#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Kling API 客户端模块

封装对 Kling API 的所有调用，提供统一的接口
"""

import asyncio
import aiohttp
import time
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin
import json

from .config import settings
from .logger import get_kling_client_logger, log_exception, log_performance

logger = get_kling_client_logger()

class KlingAPIError(Exception):
    """Kling API 异常类"""
    def __init__(self, message: str, status_code: int = None, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)

class KlingAPIClient:
    """Kling API 客户端"""
    
    def __init__(self):
        self.base_url = settings.kling.api_base_url
        self.timeout = settings.kling.request_timeout
        self.max_retries = settings.kling.max_retries
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Kling API 端点映射
        self.endpoints = {
            "text_to_image": "/kling/v1/images/generations",
            "text_to_video": "/kling/v1/videos/text2video", 
            "image_to_video": "/kling/v1/videos/image2video",
            "virtual_try_on": "/kling/v1/images/kolors-virtual-try-on",
            # 任务查询端点需要根据任务类型动态构建，这里仅作为模板
            "task_query_templates": {
                "text_to_image": "/kling/v1/images/generations/{task_id}",
                "text_to_video": "/kling/v1/videos/text2video/{task_id}",
                "image_to_video": "/kling/v1/videos/image2video/{task_id}",
                "virtual_try_on": "/kling/v1/images/kolors-virtual-try-on/{task_id}"
            }
        }
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建HTTP会话"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            connector = aiohttp.TCPConnector(
                limit=settings.performance.max_pool_connections,
                limit_per_host=settings.performance.max_pool_connections_per_host,
                ttl_dns_cache=settings.performance.dns_cache_ttl
            )
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={
                    "Content-Type": "application/json",
                    # 基础头部，具体请求时会被覆盖
                    "Accept": "application/json",
                    "Cache-Control": "no-cache"
                }
            )
        return self.session
    
    async def close(self):
        """关闭HTTP会话"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        api_key: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送HTTP请求到Kling API
        
        Args:
            method: HTTP方法
            endpoint: API端点
            api_key: API密钥
            data: 请求数据
            params: 查询参数
            **kwargs: 其他参数
            
        Returns:
            API响应数据
            
        Raises:
            KlingAPIError: API调用失败
        """
        start_time = time.time()
        url = urljoin(self.base_url, endpoint)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            # 模拟浏览器请求头，符合API网关要求
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }
        
        session = await self._get_session()
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data if method.upper() != 'GET' else None,
                    params=params,
                    **kwargs
                ) as response:
                    response_text = await response.text()
                    duration = time.time() - start_time
                    
                    log_performance(
                        logger, 
                        f"{method} {endpoint}",
                        duration,
                        status_code=response.status,
                        attempt=attempt + 1
                    )
                    
                    if response.status == 200:
                        try:
                            return await response.json()
                        except json.JSONDecodeError:
                            return {"result": response_text}
                    else:
                        error_data = {}
                        try:
                            error_data = await response.json()
                        except:
                            pass
                            
                        error_message = error_data.get("error", {}).get("message", response_text)
                        error_code = error_data.get("error", {}).get("code")
                        
                        if response.status >= 500 and attempt < self.max_retries:
                            logger.warning(f"Server error {response.status}, retrying...")
                            await asyncio.sleep(2 ** attempt)  # 指数退避
                            continue
                        
                        raise KlingAPIError(
                            message=f"Kling API error: {error_message}",
                            status_code=response.status,
                            error_code=error_code
                        )
                        
            except aiohttp.ClientError as e:
                logger.warning(f"Network error: {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise KlingAPIError(f"Network error: {str(e)}")
            
            except Exception as e:
                log_exception(logger, e, f"Request to {endpoint}")
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise KlingAPIError(f"Unexpected error: {str(e)}")
        
        raise KlingAPIError("Max retries exceeded")
    
    # =============================================================================
    # Kling API 方法实现
    # =============================================================================
    
    async def create_text_to_image(
        self,
        api_key: str,
        prompt: str,
        aspect_ratio: Optional[str] = "1:1",
        negative_prompt: Optional[str] = None,
        cfg_scale: Optional[float] = 7.5,
        seed: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        文生图
        
        Args:
            api_key: API密钥
            prompt: 文本描述
            aspect_ratio: 宽高比
            negative_prompt: 负面提示词
            cfg_scale: CFG缩放
            seed: 随机种子
            **kwargs: 其他参数
            
        Returns:
            任务创建结果
        """
        data = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "cfg_scale": cfg_scale
        }
        
        if negative_prompt:
            data["negative_prompt"] = negative_prompt
        if seed is not None:
            data["seed"] = seed
            
        data.update(kwargs)
        
        return await self._make_request(
            "POST",
            self.endpoints["text_to_image"],
            api_key,
            data=data
        )
    
    async def create_text_to_video(
        self,
        api_key: str,
        prompt: str,
        aspect_ratio: Optional[str] = "16:9",
        duration: Optional[int] = 5,
        cfg_scale: Optional[float] = 7.5,
        seed: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        文生视频
        
        Args:
            api_key: API密钥
            prompt: 文本描述
            aspect_ratio: 宽高比
            duration: 视频时长（秒）
            cfg_scale: CFG缩放
            seed: 随机种子
            **kwargs: 其他参数
            
        Returns:
            任务创建结果
        """
        data = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "duration": str(duration),  # 文档要求字符串格式
            "cfg_scale": cfg_scale,
            "model_name": "kling-v1-6",  # 必需参数
            "mode": "std"  # 必需参数：std（高性能）或 pro（高表现）
        }
        
        if seed is not None:
            data["seed"] = seed
            
        data.update(kwargs)
        
        return await self._make_request(
            "POST",
            self.endpoints["text_to_video"],
            api_key,
            data=data
        )
    
    async def create_image_to_video(
        self,
        api_key: str,
        image_url: str,
        prompt: Optional[str] = None,
        duration: Optional[int] = 5,
        cfg_scale: Optional[float] = 7.5,
        seed: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        图生视频
        
        Args:
            api_key: API密钥
            image_url: 图片URL
            prompt: 文本描述（可选）
            duration: 视频时长（秒）
            cfg_scale: CFG缩放
            seed: 随机种子
            **kwargs: 其他参数
            
        Returns:
            任务创建结果
        """
        data = {
            "image": image_url,  # API文档使用 'image' 字段
            "duration": str(duration),  # 字符串格式
            "cfg_scale": cfg_scale,
            "model_name": "kling-v1-6",  # 必需参数
            "mode": "std",  # 必需参数
            "aspect_ratio": "16:9",  # 必需参数
            "negative_prompt": ""  # 必需参数，可以为空字符串
        }
        
        if prompt:
            data["prompt"] = prompt
        if seed is not None:
            data["seed"] = seed
            
        data.update(kwargs)
        
        return await self._make_request(
            "POST",
            self.endpoints["image_to_video"],
            api_key,
            data=data
        )
    
    async def create_virtual_try_on(
        self,
        api_key: str,
        person_image: str,
        garment_image: str,
        category: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        虚拟换衣
        
        Args:
            api_key: API密钥
            person_image: 人物图片URL
            garment_image: 服装图片URL
            category: 服装类别
            **kwargs: 其他参数
            
        Returns:
            任务创建结果
        """
        data = {
            "human_image": person_image,  # API文档使用 'human_image' 字段
            "cloth_image": garment_image,  # API文档使用 'cloth_image' 字段
            "mode_name": "kolors-virtual-try-on"  # 必需参数
        }
        data.update(kwargs)
        
        return await self._make_request(
            "POST",
            self.endpoints["virtual_try_on"],
            api_key,
            data=data
        )
    
    async def get_task_info(
        self,
        api_key: str,
        task_id: str,
        task_type: str  # "text_to_image", "text_to_video", "image_to_video", "virtual_try_on"
    ) -> Dict[str, Any]:
        """
        获取任务完整信息（状态+结果）
        
        Args:
            api_key: API密钥
            task_id: 任务ID
            task_type: 任务类型
            
        Returns:
            任务完整信息
        """
        # 使用端点模板构建正确的路径
        if task_type not in self.endpoints["task_query_templates"]:
            raise ValueError(f"Unsupported task type: {task_type}")
        
        endpoint_template = self.endpoints["task_query_templates"][task_type]
        endpoint = endpoint_template.format(task_id=task_id)
        
        logger.debug(f"Querying task {task_id} with endpoint: {endpoint}")
        
        return await self._make_request(
            "GET",
            endpoint,
            api_key
        )
    
    # 为了向后兼容，保留原有方法名但使用新的实现
    async def get_task_status(
        self,
        api_key: str,
        task_id: str,
        task_type: str = "text_to_image"  # 默认值，需要调用时明确指定
    ) -> Dict[str, Any]:
        """获取任务状态（向后兼容方法）"""
        return await self.get_task_info(api_key, task_id, task_type)
    
    async def get_task_result(
        self,
        api_key: str,
        task_id: str,
        task_type: str = "text_to_image"  # 默认值，需要调用时明确指定
    ) -> Dict[str, Any]:
        """获取任务结果（向后兼容方法）"""
        return await self.get_task_info(api_key, task_id, task_type)
    
    async def get_single_task(
        self,
        api_key: str,
        task_id: str,
        task_type: str = "text_to_image"  # 默认值，需要调用时明确指定
    ) -> Dict[str, Any]:
        """查询单个任务完整信息（向后兼容方法）"""
        return await self.get_task_info(api_key, task_id, task_type)

# 全局客户端实例
_client_instance = None

async def get_kling_client() -> KlingAPIClient:
    """获取全局Kling API客户端实例"""
    global _client_instance
    if _client_instance is None:
        _client_instance = KlingAPIClient()
    return _client_instance

async def cleanup_kling_client():
    """清理全局客户端实例"""
    global _client_instance
    if _client_instance:
        await _client_instance.close()
        _client_instance = None