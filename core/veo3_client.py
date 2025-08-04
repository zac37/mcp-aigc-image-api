#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Google Vertex AI Veo3 视频生成客户端

提供Veo3视频生成的完整功能，包括：
- 认证管理
- 视频生成任务创建
- 任务状态查询
- 轮询等待完成
- 错误处理和重试机制
"""

import json
import os
import time
import asyncio
from typing import Dict, Any, Tuple, Optional, Union
import requests
import aiohttp
from google.auth import default
from google.auth.transport.requests import Request

from .simple_config import settings
from .logger import get_api_logger

logger = get_api_logger()


class Veo3APIError(Exception):
    """Veo3 API异常类"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class Veo3Client:
    """Vertex AI Veo3视频生成客户端"""
    
    def __init__(self):
        """初始化Veo3客户端"""
        self.credentials = None
        self.project_id = settings.veo3_project_id
        self.location = settings.veo3_location
        self.credentials_path = settings.google_credentials_path
        self.base_url = f"https://{self.location}-aiplatform.googleapis.com/v1"
        self.model_id = "veo-3.0-generate-preview"
        
        # 设置环境变量
        if self.credentials_path and os.path.exists(self.credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_path
        
        logger.info(f"初始化Veo3客户端 - 项目: {self.project_id}, 位置: {self.location}")
    
    def _get_credentials(self):
        """获取并初始化凭据对象"""
        if self.credentials is None:
            try:
                # 从凭据文件获取项目ID
                if not os.path.exists(self.credentials_path):
                    raise Veo3APIError(f"凭据文件不存在: {self.credentials_path}")
                
                with open(self.credentials_path, 'r') as f:
                    creds_data = json.load(f)
                
                self.project_id = creds_data.get('project_id', self.project_id)
                
                # 获取默认凭据
                self.credentials, _ = default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
                logger.info(f"凭据初始化成功 - 项目: {self.project_id}")
                
            except Exception as e:
                logger.error(f"凭据初始化失败: {e}")
                raise Veo3APIError(f"凭据初始化失败: {e}")
        
        return self.credentials
    
    def get_access_token(self) -> str:
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
                raise Veo3APIError(f"令牌刷新失败: {e}")
        
        return credentials.token
    
    def create_video(
        self, 
        prompt: str, 
        duration: int = 5, 
        aspect_ratio: str = "16:9", 
        **kwargs
    ) -> str:
        """
        创建视频生成任务
        
        Args:
            prompt: 视频生成提示词
            duration: 视频时长(秒)，默认5秒
            aspect_ratio: 宽高比，默认16:9
            **kwargs: 其他可选参数
        
        Returns:
            operation_id: 任务操作ID
        """
        try:
            access_token = self.get_access_token()
            
            url = (f"{self.base_url}/projects/{self.project_id}/locations/{self.location}/"
                  f"publishers/google/models/{self.model_id}:predictLongRunning")
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json; charset=utf-8'
            }
            
            # 构建参数
            params = {
                "sampleCount": 1,
                "durationSeconds": 8,  # Veo3目前只支持8秒
                "aspectRatio": aspect_ratio,
                **kwargs
            }
            
            # 如果没有提供storageUri，添加默认值以获取GCS URL而不是base64数据
            if 'storageUri' not in params and 'storageUri' not in kwargs:
                import time
                timestamp = int(time.time())
                params['storageUri'] = f"gs://{settings.veo3_storage_bucket}/veo3-videos/{timestamp}/"
            
            # 移除空值
            params = {k: v for k, v in params.items() if v is not None}
            
            payload = {
                "instances": [{"prompt": prompt}],
                "parameters": params
            }
            
            logger.info(f"提交Veo3视频生成任务 - 提示词: {prompt[:50]}..., 时长: {duration}s, 宽高比: {aspect_ratio}")
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                operation_id = result.get('name')
                logger.info(f"任务已提交 - ID: {operation_id}")
                return operation_id
            else:
                self._handle_api_error(response)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求失败: {e}")
            raise Veo3APIError(f"网络请求失败: {e}")
        except Exception as e:
            logger.error(f"创建视频任务失败: {e}")
            raise Veo3APIError(f"创建视频任务失败: {e}")
    
    async def create_video_async(
        self, 
        prompt: str, 
        duration: int = 5, 
        aspect_ratio: str = "16:9", 
        **kwargs
    ) -> str:
        """
        异步创建视频生成任务
        
        Args:
            prompt: 视频生成提示词
            duration: 视频时长(秒)，默认5秒
            aspect_ratio: 宽高比，默认16:9
            **kwargs: 其他可选参数
        
        Returns:
            operation_id: 任务操作ID
        """
        try:
            access_token = self.get_access_token()
            
            url = (f"{self.base_url}/projects/{self.project_id}/locations/{self.location}/"
                  f"publishers/google/models/{self.model_id}:predictLongRunning")
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json; charset=utf-8'
            }
            
            # 构建参数
            params = {
                "sampleCount": 1,
                "durationSeconds": 8,  # Veo3目前只支持8秒
                "aspectRatio": aspect_ratio,
                **kwargs
            }
            
            # 如果没有提供storageUri，添加默认值以获取GCS URL而不是base64数据
            if 'storageUri' not in params and 'storageUri' not in kwargs:
                import time
                timestamp = int(time.time())
                params['storageUri'] = f"gs://{settings.veo3_storage_bucket}/veo3-videos/{timestamp}/"
            
            # 移除空值
            params = {k: v for k, v in params.items() if v is not None}
            
            payload = {
                "instances": [{"prompt": prompt}],
                "parameters": params
            }
            
            logger.info(f"异步提交Veo3视频生成任务 - 提示词: {prompt[:50]}...")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        operation_id = result.get('name')
                        logger.info(f"异步任务已提交 - ID: {operation_id}")
                        return operation_id
                    else:
                        error_text = await response.text()
                        logger.error(f"异步API调用失败: {response.status} - {error_text}")
                        raise Veo3APIError(f"API调用失败: {response.status} - {error_text}")
                        
        except asyncio.TimeoutError:
            logger.error("异步请求超时")
            raise Veo3APIError("请求超时")
        except Exception as e:
            logger.error(f"异步创建视频任务失败: {e}")
            raise Veo3APIError(f"异步创建视频任务失败: {e}")
    
    def check_status(self, operation_id: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        检查任务状态
        
        Args:
            operation_id: 任务操作ID
        
        Returns:
            status: 任务状态 ('running', 'completed', 'failed')
            data: 任务数据（成功时为结果，失败时为错误信息）
        """
        try:
            access_token = self.get_access_token()
            
            # 使用fetchPredictOperation API来查询状态
            url = (f"{self.base_url}/projects/{self.project_id}/locations/{self.location}/"
                  f"publishers/google/models/{self.model_id}:fetchPredictOperation")
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json; charset=utf-8'
            }
            
            payload = {
                "operationName": operation_id
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('done', False):
                    if 'response' in result:
                        logger.info(f"任务完成 - ID: {operation_id}")
                        return 'completed', result['response']
                    elif 'error' in result:
                        logger.error(f"任务失败 - ID: {operation_id}, 错误: {result['error']}")
                        return 'failed', result['error']
                else:
                    return 'running', None
            else:
                self._handle_api_error(response)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"状态查询网络错误: {e}")
            raise Veo3APIError(f"状态查询网络错误: {e}")
        except Exception as e:
            logger.error(f"状态查询失败: {e}")
            raise Veo3APIError(f"状态查询失败: {e}")
    
    async def check_status_async(self, operation_id: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """异步检查任务状态"""
        try:
            access_token = self.get_access_token()
            
            # 使用fetchPredictOperation API来查询状态
            url = (f"{self.base_url}/projects/{self.project_id}/locations/{self.location}/"
                  f"publishers/google/models/{self.model_id}:fetchPredictOperation")
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json; charset=utf-8'
            }
            
            payload = {
                "operationName": operation_id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if result.get('done', False):
                            if 'response' in result:
                                logger.info(f"异步任务完成 - ID: {operation_id}")
                                return 'completed', result['response']
                            elif 'error' in result:
                                logger.error(f"异步任务失败 - ID: {operation_id}, 错误: {result['error']}")
                                return 'failed', result['error']
                        else:
                            return 'running', None
                    else:
                        error_text = await response.text()
                        logger.error(f"异步状态查询失败: {response.status} - {error_text}")
                        raise Veo3APIError(f"状态查询失败: {response.status} - {error_text}", status_code=response.status)
                        
        except asyncio.TimeoutError:
            logger.error("异步状态查询超时")
            raise Veo3APIError("状态查询超时")
        except Exception as e:
            logger.error(f"异步状态查询失败: {e}")
            # 检查是否是404错误（任务过期）
            error_str = str(e)
            if "404" in error_str:
                raise Veo3APIError(f"异步状态查询失败: {e}", status_code=404)
            else:
                raise Veo3APIError(f"异步状态查询失败: {e}")
    
    def wait_for_completion(
        self, 
        operation_id: str, 
        max_wait: int = 600, 
        check_interval: int = 15
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        等待任务完成
        
        Args:
            operation_id: 任务操作ID
            max_wait: 最大等待时间(秒)，默认600秒
            check_interval: 检查间隔(秒)，默认15秒
        
        Returns:
            success: 是否成功完成
            result: 任务结果或错误信息
        """
        start_time = time.time()
        attempts = 0
        max_attempts = max_wait // check_interval
        
        logger.info(f"开始等待任务完成 - ID: {operation_id}, 最大等待: {max_wait}s")
        
        while attempts < max_attempts:
            try:
                status, data = self.check_status(operation_id)
                
                if status == 'completed':
                    elapsed = time.time() - start_time
                    logger.info(f"任务完成! 耗时: {elapsed:.1f}秒 - ID: {operation_id}")
                    return True, data
                    
                elif status == 'failed':
                    logger.error(f"任务失败 - ID: {operation_id}: {data}")
                    return False, data
                    
                elif status == 'running':
                    elapsed = time.time() - start_time
                    logger.info(f"任务运行中... ({elapsed:.1f}s) - ID: {operation_id}")
                    time.sleep(check_interval)
                    attempts += 1
                    
            except Exception as e:
                logger.warning(f"检查状态出错: {e}, 继续等待...")
                time.sleep(check_interval)
                attempts += 1
        
        logger.warning(f"等待超时 - ID: {operation_id}")
        return False, None
    
    async def wait_for_completion_async(
        self, 
        operation_id: str, 
        max_wait: int = 600, 
        check_interval: int = 15
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """异步等待任务完成"""
        start_time = time.time()
        attempts = 0
        max_attempts = max_wait // check_interval
        
        logger.info(f"开始异步等待任务完成 - ID: {operation_id}")
        
        while attempts < max_attempts:
            try:
                status, data = await self.check_status_async(operation_id)
                
                if status == 'completed':
                    elapsed = time.time() - start_time
                    logger.info(f"异步任务完成! 耗时: {elapsed:.1f}秒 - ID: {operation_id}")
                    return True, data
                    
                elif status == 'failed':
                    logger.error(f"异步任务失败 - ID: {operation_id}: {data}")
                    return False, data
                    
                elif status == 'running':
                    elapsed = time.time() - start_time
                    logger.info(f"异步任务运行中... ({elapsed:.1f}s) - ID: {operation_id}")
                    await asyncio.sleep(check_interval)
                    attempts += 1
                    
            except Exception as e:
                logger.warning(f"异步检查状态出错: {e}, 继续等待...")
                await asyncio.sleep(check_interval)
                attempts += 1
        
        logger.warning(f"异步等待超时 - ID: {operation_id}")
        return False, None
    
    def _handle_api_error(self, response: requests.Response):
        """处理API错误响应"""
        status_code = response.status_code
        error_text = response.text
        
        if status_code == 401:
            logger.error("认证失败 - 访问令牌无效")
            # 清除缓存的令牌，下次请求时重新获取
            self.access_token = None
            raise Veo3APIError("认证失败 - 请检查访问令牌")
        
        elif status_code == 403:
            if 'BILLING_DISABLED' in error_text:
                logger.error("项目计费未启用")
                raise Veo3APIError("项目计费未启用 - 请在Google Cloud Console启用计费")
            else:
                logger.error("权限不足")
                raise Veo3APIError("权限不足 - 请检查服务账户权限")
        
        elif status_code == 404:
            logger.error("API端点不存在")
            raise Veo3APIError("API端点不存在 - 请检查项目ID和模型名称")
        
        elif status_code == 429:
            logger.error("请求频率过高")
            raise Veo3APIError("请求频率过高 - 请稍后重试")
        
        else:
            logger.error(f"API调用失败: {status_code} - {error_text}")
            raise Veo3APIError(f"API调用失败: {status_code} - {error_text}")
    
    def generate_video(
        self, 
        prompt: str, 
        duration: int = 5, 
        aspect_ratio: str = "16:9",
        wait_for_completion: bool = True,
        max_wait: int = 600,
        **kwargs
    ) -> Dict[str, Any]:
        """
        完整的视频生成流程
        
        Args:
            prompt: 视频生成提示词
            duration: 视频时长(秒)
            aspect_ratio: 宽高比
            wait_for_completion: 是否等待完成
            max_wait: 最大等待时间
            **kwargs: 其他参数
        
        Returns:
            result: 包含operation_id和结果的字典
        """
        try:
            # 创建任务
            operation_id = self.create_video(
                prompt=prompt,
                duration=duration,
                aspect_ratio=aspect_ratio,
                **kwargs
            )
            
            result = {
                'operation_id': operation_id,
                'status': 'submitted',
                'prompt': prompt,
                'duration': duration,
                'aspect_ratio': aspect_ratio
            }
            
            # 如果需要等待完成
            if wait_for_completion:
                success, data = self.wait_for_completion(operation_id, max_wait)
                
                if success:
                    result['status'] = 'completed'
                    result['data'] = data
                    # 尝试提取视频URL - 使用官方API格式
                    if data and 'generatedSamples' in data:
                        samples = data['generatedSamples']
                        if samples and len(samples) > 0:
                            sample = samples[0]
                            if 'video' in sample and 'uri' in sample['video']:
                                result['video_url'] = sample['video']['uri']
                else:
                    result['status'] = 'failed'
                    result['error'] = data
            
            return result
            
        except Exception as e:
            logger.error(f"视频生成流程失败: {e}")
            raise Veo3APIError(f"视频生成流程失败: {e}")
    
    async def generate_video_async(
        self, 
        prompt: str, 
        duration: int = 5, 
        aspect_ratio: str = "16:9",
        wait_for_completion: bool = True,
        max_wait: int = 600,
        **kwargs
    ) -> Dict[str, Any]:
        """异步完整的视频生成流程"""
        try:
            # 创建任务
            operation_id = await self.create_video_async(
                prompt=prompt,
                duration=duration,
                aspect_ratio=aspect_ratio,
                **kwargs
            )
            
            result = {
                'operation_id': operation_id,
                'status': 'submitted',
                'prompt': prompt,
                'duration': duration,
                'aspect_ratio': aspect_ratio
            }
            
            # 如果需要等待完成
            if wait_for_completion:
                success, data = await self.wait_for_completion_async(operation_id, max_wait)
                
                if success:
                    result['status'] = 'completed'
                    result['data'] = data
                    # 尝试提取视频URL - 使用官方API格式
                    if data and 'generatedSamples' in data:
                        samples = data['generatedSamples']
                        if samples and len(samples) > 0:
                            sample = samples[0]
                            if 'video' in sample and 'uri' in sample['video']:
                                result['video_url'] = sample['video']['uri']
                else:
                    result['status'] = 'failed'
                    result['error'] = data
            
            return result
            
        except Exception as e:
            logger.error(f"异步视频生成流程失败: {e}")
            raise Veo3APIError(f"异步视频生成流程失败: {e}")


# 创建全局Veo3客户端实例
veo3_client = Veo3Client()