#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Kling 服务层

提供Kling API的高级业务逻辑封装
"""

from typing import Dict, List, Optional, Any, Union
import asyncio
from datetime import datetime

from core.kling_client import get_kling_client, KlingAPIError
from core.logger import get_api_logger, log_exception
from core.config import settings

logger = get_api_logger()

class KlingService:
    """Kling API 服务类"""
    
    def __init__(self):
        self.client = None
    
    async def _get_client(self):
        """获取Kling客户端"""
        if self.client is None:
            self.client = await get_kling_client()
        return self.client
    
    def _get_api_key(self) -> str:
        """从配置中获取API密钥"""
        return settings.kling.api_key
    
    async def create_text_to_image_task(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        negative_prompt: Optional[str] = None,
        cfg_scale: float = 7.5,
        seed: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建文生图任务
        
        Args:
            prompt: 文本描述
            aspect_ratio: 宽高比 (支持: "1:1", "16:9", "9:16", "4:3", "3:4")
            negative_prompt: 负面提示词
            cfg_scale: CFG缩放 (范围: 1.0-20.0)
            seed: 随机种子
            **kwargs: 其他参数
            
        Returns:
            任务创建结果
        """
        try:
            client = await self._get_client()
            api_key = self._get_api_key()
            
            # 参数验证
            if not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            valid_ratios = ["1:1", "16:9", "9:16", "4:3", "3:4"]
            if aspect_ratio not in valid_ratios:
                raise ValueError(f"Invalid aspect_ratio. Must be one of: {valid_ratios}")
            
            if not (0.0 <= cfg_scale <= 1.0):
                raise ValueError("cfg_scale must be between 0.0 and 1.0")
            
            logger.info(f"Creating text-to-image task with prompt: {prompt[:100]}...")
            
            result = await client.create_text_to_image(
                api_key=api_key,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                negative_prompt=negative_prompt,
                cfg_scale=cfg_scale,
                seed=seed,
                **kwargs
            )
            
            logger.info(f"Text-to-image task created successfully: {result.get('task_id', 'N/A')}")
            return result
            
        except Exception as e:
            log_exception(logger, e, "Failed to create text-to-image task")
            raise
    
    async def create_text_to_video_task(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        duration: int = 5,
        cfg_scale: float = 7.5,
        seed: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建文生视频任务
        
        Args:
            prompt: 文本描述
            aspect_ratio: 宽高比 (支持: "16:9", "9:16", "1:1")
            duration: 视频时长，单位秒 (支持: 5, 10)
            cfg_scale: CFG缩放 (范围: 1.0-20.0)
            seed: 随机种子
            **kwargs: 其他参数
            
        Returns:
            任务创建结果
        """
        try:
            client = await self._get_client()
            api_key = self._get_api_key()
            
            # 参数验证
            if not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            valid_ratios = ["16:9", "9:16", "1:1"]
            if aspect_ratio not in valid_ratios:
                raise ValueError(f"Invalid aspect_ratio. Must be one of: {valid_ratios}")
            
            valid_durations = [5, 10]
            if duration not in valid_durations:
                raise ValueError(f"Invalid duration. Must be one of: {valid_durations}")
            
            if not (0.0 <= cfg_scale <= 1.0):
                raise ValueError("cfg_scale must be between 0.0 and 1.0")
            
            logger.info(f"Creating text-to-video task with prompt: {prompt[:100]}...")
            
            result = await client.create_text_to_video(
                api_key=api_key,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                duration=duration,
                cfg_scale=cfg_scale,
                seed=seed,
                **kwargs
            )
            
            logger.info(f"Text-to-video task created successfully: {result.get('task_id', 'N/A')}")
            return result
            
        except Exception as e:
            log_exception(logger, e, "Failed to create text-to-video task")
            raise
    
    async def create_image_to_video_task(
        self,
        image_url: str,
        prompt: Optional[str] = None,
        duration: int = 5,
        cfg_scale: float = 7.5,
        seed: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建图生视频任务
        
        Args:
            image_url: 输入图片的URL
            prompt: 文本描述（可选，用于指导视频生成）
            duration: 视频时长，单位秒 (支持: 5, 10)
            cfg_scale: CFG缩放 (范围: 1.0-20.0)
            seed: 随机种子
            **kwargs: 其他参数
            
        Returns:
            任务创建结果
        """
        try:
            client = await self._get_client()
            api_key = self._get_api_key()
            
            # 参数验证
            if not image_url.strip():
                raise ValueError("Image URL cannot be empty")
            
            if not image_url.startswith(('http://', 'https://')):
                raise ValueError("Invalid image URL format")
            
            valid_durations = [5, 10]
            if duration not in valid_durations:
                raise ValueError(f"Invalid duration. Must be one of: {valid_durations}")
            
            if not (0.0 <= cfg_scale <= 1.0):
                raise ValueError("cfg_scale must be between 0.0 and 1.0")
            
            logger.info(f"Creating image-to-video task with image: {image_url}")
            
            result = await client.create_image_to_video(
                api_key=api_key,
                image_url=image_url,
                prompt=prompt,
                duration=duration,
                cfg_scale=cfg_scale,
                seed=seed,
                **kwargs
            )
            
            logger.info(f"Image-to-video task created successfully: {result.get('task_id', 'N/A')}")
            return result
            
        except Exception as e:
            log_exception(logger, e, "Failed to create image-to-video task")
            raise
    
    async def create_virtual_try_on_task(
        self,
        person_image: str,
        garment_image: str,
        category: str = "tops",
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建虚拟换衣任务
        
        Args:
            person_image: 人物图片URL
            garment_image: 服装图片URL
            category: 服装类别 (支持: "tops", "bottoms", "dresses", "outerwear")
            **kwargs: 其他参数
            
        Returns:
            任务创建结果
        """
        try:
            client = await self._get_client()
            api_key = self._get_api_key()
            
            # 参数验证
            if not person_image.strip() or not garment_image.strip():
                raise ValueError("Person image and garment image URLs cannot be empty")
            
            if not all(url.startswith(('http://', 'https://')) for url in [person_image, garment_image]):
                raise ValueError("Invalid image URL format")
            
            valid_categories = ["tops", "bottoms", "dresses", "outerwear"]
            if category not in valid_categories:
                raise ValueError(f"Invalid category. Must be one of: {valid_categories}")
            
            logger.info(f"Creating virtual try-on task: {category}")
            
            result = await client.create_virtual_try_on(
                api_key=api_key,
                person_image=person_image,
                garment_image=garment_image,
                category=category,
                **kwargs
            )
            
            logger.info(f"Virtual try-on task created successfully: {result.get('task_id', 'N/A')}")
            return result
            
        except Exception as e:
            log_exception(logger, e, "Failed to create virtual try-on task")
            raise
    
    async def _try_all_task_types(self, client, task_id: str, method_name: str) -> Dict[str, Any]:
        """
        尝试所有可能的任务类型来查询任务
        
        Args:
            client: Kling客户端实例
            task_id: 任务ID
            method_name: 要调用的方法名
            
        Returns:
            任务信息
        """
        api_key = self._get_api_key()
        task_types = ["text_to_image", "text_to_video", "image_to_video", "virtual_try_on"]
        errors = {}
        
        logger.debug(f"Trying to find task {task_id} across all task types")
        
        for task_type in task_types:
            try:
                # 使用统一的 get_task_info 方法
                if method_name in ["get_task_status", "get_task_result", "get_single_task"]:
                    result = await client.get_task_info(api_key=api_key, task_id=task_id, task_type=task_type)
                    logger.info(f"Successfully found task {task_id} as {task_type}")
                    return result
                else:
                    # 如果是其他方法，仍然使用原来的方式
                    method = getattr(client, method_name)
                    result = await method(api_key=api_key, task_id=task_id, task_type=task_type)
                    logger.info(f"Successfully found task {task_id} as {task_type}")
                    return result
            except KlingAPIError as e:
                errors[task_type] = f"API Error: {e.message}"
                logger.debug(f"Task {task_id} not found as {task_type}: {e.message}")
                # 如果是404错误，继续尝试下一个类型；如果是其他错误，可能需要直接抛出
                if e.status_code and e.status_code != 404:
                    logger.warning(f"Non-404 error for task {task_id} as {task_type}: {e.message}")
                continue
            except Exception as e:
                errors[task_type] = f"Unexpected error: {str(e)}"
                logger.debug(f"Task {task_id} failed as {task_type}: {str(e)}")
                continue
        
        # 如果所有类型都失败了，生成详细的错误信息
        error_summary = "; ".join([f"{task_type}: {error}" for task_type, error in errors.items()])
        raise KlingAPIError(f"Task {task_id} not found with any task type. Errors: {error_summary}", status_code=404)

    async def get_task_status(
        self,
        task_id: str,
        task_type: str = None
    ) -> Dict[str, Any]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            task_type: 任务类型（可选，会尝试自动检测）
            
        Returns:
            任务状态信息
        """
        try:
            client = await self._get_client()
            api_key = self._get_api_key()
            
            if not task_id.strip():
                raise ValueError("Task ID cannot be empty")
            
            logger.debug(f"Getting status for task: {task_id}")
            
            # 如果没有指定任务类型，尝试所有可能的类型
            if task_type:
                result = await client.get_task_status(api_key=api_key, task_id=task_id, task_type=task_type)
            else:
                result = await self._try_all_task_types(client, task_id, "get_task_status")
            
            logger.debug(f"Task {task_id} status: {result.get('data', {}).get('task_status', 'unknown')}")
            return result
            
        except Exception as e:
            log_exception(logger, e, f"Failed to get task status for {task_id}")
            raise
    
    async def get_task_result(
        self,
        task_id: str,
        task_type: str = None
    ) -> Dict[str, Any]:
        """
        获取任务结果
        
        Args:
            task_id: 任务ID
            task_type: 任务类型（可选，会尝试自动检测）
            
        Returns:
            任务结果信息
        """
        try:
            client = await self._get_client()
            api_key = self._get_api_key()
            
            if not task_id.strip():
                raise ValueError("Task ID cannot be empty")
            
            logger.debug(f"Getting result for task: {task_id}")
            
            # 如果没有指定任务类型，尝试所有可能的类型
            if task_type:
                result = await client.get_task_result(api_key=api_key, task_id=task_id, task_type=task_type)
            else:
                result = await self._try_all_task_types(client, task_id, "get_task_result")
            
            logger.debug(f"Task {task_id} result retrieved successfully")
            return result
            
        except Exception as e:
            log_exception(logger, e, f"Failed to get task result for {task_id}")
            raise
    
    async def get_single_task(
        self,
        task_id: str,
        task_type: str = None
    ) -> Dict[str, Any]:
        """
        获取单个任务的完整信息
        
        Args:
            task_id: 任务ID
            task_type: 任务类型（可选，会尝试自动检测）
            
        Returns:
            任务完整信息
        """
        try:
            client = await self._get_client()
            api_key = self._get_api_key()
            
            if not task_id.strip():
                raise ValueError("Task ID cannot be empty")
            
            logger.debug(f"Getting complete info for task: {task_id}")
            
            # 如果没有指定任务类型，尝试所有可能的类型
            if task_type:
                result = await client.get_single_task(api_key=api_key, task_id=task_id, task_type=task_type)
            else:
                result = await self._try_all_task_types(client, task_id, "get_single_task")
            
            logger.debug(f"Task {task_id} info retrieved successfully")
            return result
            
        except Exception as e:
            log_exception(logger, e, f"Failed to get task info for {task_id}")
            raise
    
    async def wait_for_task_completion(
        self,
        task_id: str,
        timeout: int = 300,
        poll_interval: int = 5
    ) -> Dict[str, Any]:
        """
        等待任务完成
        
        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）
            poll_interval: 轮询间隔（秒）
            
        Returns:
            任务最终结果
            
        Raises:
            TimeoutError: 任务超时
            KlingAPIError: API调用失败
        """
        start_time = datetime.now()
        
        while True:
            try:
                status_result = await self.get_task_status(task_id)
                status = status_result.get('status', '').lower()
                
                if status == 'completed':
                    logger.info(f"Task {task_id} completed successfully")
                    return await self.get_task_result(task_id)
                elif status == 'failed':
                    error_msg = status_result.get('error_message', 'Task failed')
                    logger.error(f"Task {task_id} failed: {error_msg}")
                    raise KlingAPIError(f"Task failed: {error_msg}")
                elif status in ['pending', 'processing', 'running']:
                    # 任务进行中，继续等待
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed > timeout:
                        raise TimeoutError(f"Task {task_id} timeout after {timeout} seconds")
                    
                    logger.debug(f"Task {task_id} still {status}, waiting...")
                    await asyncio.sleep(poll_interval)
                else:
                    logger.warning(f"Task {task_id} has unknown status: {status}")
                    await asyncio.sleep(poll_interval)
                    
            except (KlingAPIError, TimeoutError):
                raise
            except Exception as e:
                log_exception(logger, e, f"Error while waiting for task {task_id}")
                raise KlingAPIError(f"Error while waiting for task: {str(e)}")

# 全局服务实例
_service_instance = None

def get_kling_service() -> KlingService:
    """获取全局Kling服务实例"""
    global _service_instance
    if _service_instance is None:
        _service_instance = KlingService()
    return _service_instance