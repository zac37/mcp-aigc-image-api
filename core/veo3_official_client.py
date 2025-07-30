#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
官方Google Vertex AI Veo3客户端
"""

import os
import json
import time
import requests
from typing import Dict, Any, Optional, Tuple
from google.auth import default
from google.auth.transport.requests import Request
from core.logger import get_logger

logger = get_logger(__name__)

class Veo3OfficialClient:
    """Google Vertex AI Veo3 官方API客户端"""
    
    def __init__(self):
        self.project_id = "qhhl-veo"
        self.location = "us-central1"
        self.model_id = "veo-3.0-generate-preview"
        self._access_token = None
        self._token_expiry = 0
        
    def _get_access_token(self) -> str:
        """获取Google Cloud访问令牌"""
        # 如果令牌还有效，直接返回
        if self._access_token and time.time() < self._token_expiry:
            return self._access_token
            
        try:
            # 获取默认凭据
            credentials, _ = default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
            
            # 刷新令牌
            auth_req = Request()
            credentials.refresh(auth_req)
            
            self._access_token = credentials.token
            # 设置过期时间（提前5分钟刷新）
            self._token_expiry = time.time() + 3300  # 55分钟
            
            logger.info("成功获取Google Cloud访问令牌")
            return self._access_token
            
        except Exception as e:
            logger.error(f"获取访问令牌失败: {e}")
            raise Exception(f"获取访问令牌失败: {e}")
    
    def create_video(self, prompt: str, duration: int = 5, aspect_ratio: str = "16:9") -> str:
        """创建视频生成任务
        
        Args:
            prompt: 视频描述提示词
            duration: 视频时长（秒）
            aspect_ratio: 宽高比
            
        Returns:
            操作ID (operation_name)
        """
        access_token = self._get_access_token()
        
        # API端点
        url = (f"https://{self.location}-aiplatform.googleapis.com/v1/"
               f"projects/{self.project_id}/locations/{self.location}/"
               f"publishers/google/models/{self.model_id}:predictLongRunning")
        
        # 请求头
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # 请求体
        payload = {
            "instances": [
                {
                    "prompt": prompt
                }
            ],
            "parameters": {
                "sampleCount": 1,
                "durationSeconds": duration,
                "aspectRatio": aspect_ratio
            }
        }
        
        try:
            # 发送请求
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                operation_name = result.get('name')
                logger.info(f"视频生成任务已提交: {operation_name}")
                return operation_name
            else:
                error_msg = f"API调用失败: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP请求失败: {e}")
            raise Exception(f"HTTP请求失败: {e}")
    
    def check_status(self, operation_name: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """查询任务状态
        
        Args:
            operation_name: 操作ID
            
        Returns:
            (状态, 数据) - 状态: 'running', 'completed', 'failed'
        """
        access_token = self._get_access_token()
        
        url = f"https://{self.location}-aiplatform.googleapis.com/v1/{operation_name}"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('done', False):
                    if 'response' in result:
                        # 成功完成
                        logger.info(f"任务完成: {operation_name}")
                        return 'completed', result['response']
                    elif 'error' in result:
                        # 操作失败
                        logger.error(f"任务失败: {result['error']}")
                        return 'failed', result['error']
                else:
                    # 任务进行中
                    return 'running', None
            else:
                logger.error(f"状态查询失败: {response.status_code} - {response.text}")
                return 'failed', {'error': f"状态查询失败: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"查询任务状态失败: {e}")
            return 'failed', {'error': str(e)}
    
    def wait_for_completion(self, operation_name: str, max_wait: int = 600, 
                          check_interval: int = 10) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """等待任务完成
        
        Args:
            operation_name: 操作ID
            max_wait: 最大等待时间（秒）
            check_interval: 检查间隔（秒）
            
        Returns:
            (是否成功, 结果数据)
        """
        start_time = time.time()
        attempts = 0
        max_attempts = max_wait // check_interval
        
        logger.info(f"开始轮询任务状态: {operation_name}")
        
        while attempts < max_attempts:
            try:
                status, data = self.check_status(operation_name)
                
                if status == 'completed':
                    elapsed = time.time() - start_time
                    logger.info(f"任务完成，耗时: {elapsed:.1f}秒")
                    return True, data
                    
                elif status == 'failed':
                    logger.error("任务失败")
                    return False, data
                    
                elif status == 'running':
                    elapsed = time.time() - start_time
                    logger.debug(f"任务运行中... (已等待{elapsed:.1f}秒)")
                    time.sleep(check_interval)
                    attempts += 1
                    
            except Exception as e:
                logger.error(f"状态查询出错: {e}")
                time.sleep(check_interval)
                attempts += 1
        
        logger.warning("超过最大等待时间，任务可能仍在进行中")
        return False, None


# 全局实例
veo3_official_client = Veo3OfficialClient()