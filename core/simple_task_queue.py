#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单任务队列管理器
用于存储和管理视频生成任务信息，与Celery解耦
"""

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import redis

from core.logger import get_logger
from core.config import settings

logger = get_logger(__name__)


@dataclass
class VideoTask:
    """视频任务数据模型"""
    task_id: str
    external_task_id: str  # 外部API任务ID
    prompt: str
    model: str
    status: str = "pending"  # pending, monitoring, completed, failed
    created_at: str = ""
    updated_at: str = ""
    result_url: Optional[str] = None
    minio_url: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 处理None值，Redis不支持None
        for key, value in data.items():
            if value is None:
                data[key] = ""
            elif isinstance(value, dict):
                data[key] = json.dumps(value) if value else "{}"
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoTask':
        """从字典创建实例"""
        processed_data = data.copy()
        
        # 反序列化metadata
        if 'metadata' in processed_data and isinstance(processed_data['metadata'], str):
            try:
                processed_data['metadata'] = json.loads(processed_data['metadata']) if processed_data['metadata'] else {}
            except json.JSONDecodeError:
                processed_data['metadata'] = {}
        
        # 处理空字符串转为None
        none_fields = ['result_url', 'minio_url', 'error_message']
        for field in none_fields:
            if field in processed_data and processed_data[field] == "":
                processed_data[field] = None
        
        return cls(**processed_data)


class SimpleTaskQueue:
    """简单任务队列管理器"""
    
    # Redis键前缀
    QUEUE_PENDING = "veo3_tasks:pending"  # 待处理任务队列
    QUEUE_MONITORING = "veo3_tasks:monitoring"  # 监控中任务队列
    KEY_TASK = "veo3_task:"  # 任务详情键前缀
    
    def __init__(self):
        """初始化任务队列"""
        self.redis = redis.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            password=settings.redis.password,
            db=settings.redis.db,
            decode_responses=True,
            socket_keepalive=True,
            health_check_interval=30
        )
        
        # 测试连接
        try:
            self.redis.ping()
            logger.info("SimpleTaskQueue Redis连接成功")
        except Exception as e:
            logger.error(f"SimpleTaskQueue Redis连接失败: {e}")
            raise
    
    def add_task(self, task: VideoTask) -> bool:
        """添加任务到队列
        
        Args:
            task: 视频任务对象
            
        Returns:
            添加成功返回True
        """
        try:
            with self.redis.pipeline() as pipe:
                pipe.multi()
                
                # 存储任务详情
                pipe.hset(f"{self.KEY_TASK}{task.task_id}", mapping=task.to_dict())
                
                # 添加到待处理队列（使用当前时间戳作为score）
                pipe.zadd(self.QUEUE_PENDING, {task.task_id: int(time.time())})
                
                pipe.execute()
            
            logger.info(f"任务已添加到队列: {task.task_id} -> {task.external_task_id}")
            return True
            
        except Exception as e:
            logger.error(f"添加任务失败: {e}")
            return False
    
    def get_pending_tasks(self, limit: int = 10) -> List[VideoTask]:
        """获取待处理任务
        
        Args:
            limit: 最大返回数量
            
        Returns:
            任务列表
        """
        try:
            # 按时间顺序获取任务ID
            task_ids = self.redis.zrange(self.QUEUE_PENDING, 0, limit - 1)
            
            tasks = []
            for task_id in task_ids:
                task_data = self.redis.hgetall(f"{self.KEY_TASK}{task_id}")
                if task_data:
                    tasks.append(VideoTask.from_dict(task_data))
            
            return tasks
            
        except Exception as e:
            logger.error(f"获取待处理任务失败: {e}")
            return []
    
    def move_to_monitoring(self, task_id: str) -> bool:
        """将任务移动到监控队列
        
        Args:
            task_id: 任务ID
            
        Returns:
            移动成功返回True
        """
        try:
            with self.redis.pipeline() as pipe:
                pipe.multi()
                
                # 从待处理队列移除
                pipe.zrem(self.QUEUE_PENDING, task_id)
                
                # 添加到监控队列
                pipe.zadd(self.QUEUE_MONITORING, {task_id: int(time.time())})
                
                # 更新任务状态
                pipe.hset(f"{self.KEY_TASK}{task_id}", "status", "monitoring")
                pipe.hset(f"{self.KEY_TASK}{task_id}", "updated_at", datetime.now(timezone.utc).isoformat())
                
                pipe.execute()
            
            logger.debug(f"任务移动到监控队列: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"移动任务到监控队列失败: {e}")
            return False
    
    def get_monitoring_tasks(self, limit: int = 50) -> List[VideoTask]:
        """获取监控中的任务
        
        Args:
            limit: 最大返回数量
            
        Returns:
            任务列表
        """
        try:
            task_ids = self.redis.zrange(self.QUEUE_MONITORING, 0, limit - 1)
            
            tasks = []
            for task_id in task_ids:
                task_data = self.redis.hgetall(f"{self.KEY_TASK}{task_id}")
                if task_data:
                    tasks.append(VideoTask.from_dict(task_data))
            
            return tasks
            
        except Exception as e:
            logger.error(f"获取监控任务失败: {e}")
            return []
    
    def update_task(self, task_id: str, **updates) -> bool:
        """更新任务信息
        
        Args:
            task_id: 任务ID
            **updates: 要更新的字段
            
        Returns:
            更新成功返回True
        """
        try:
            # 添加更新时间
            updates['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # 处理复杂类型
            for key, value in updates.items():
                if isinstance(value, dict):
                    updates[key] = json.dumps(value)
                elif value is None:
                    updates[key] = ""
            
            self.redis.hmset(f"{self.KEY_TASK}{task_id}", updates)
            
            logger.debug(f"任务已更新: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新任务失败: {e}")
            return False
    
    def complete_task(self, task_id: str, result_url: Optional[str] = None, minio_url: Optional[str] = None) -> bool:
        """标记任务完成
        
        Args:
            task_id: 任务ID
            result_url: 原始结果URL
            minio_url: MinIO存储URL
            
        Returns:
            完成成功返回True
        """
        try:
            with self.redis.pipeline() as pipe:
                pipe.multi()
                
                # 从监控队列移除
                pipe.zrem(self.QUEUE_MONITORING, task_id)
                
                # 更新任务状态
                updates = {
                    "status": "completed",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                if result_url:
                    updates["result_url"] = result_url
                if minio_url:
                    updates["minio_url"] = minio_url
                
                pipe.hmset(f"{self.KEY_TASK}{task_id}", updates)
                
                pipe.execute()
            
            logger.info(f"任务已完成: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"完成任务失败: {e}")
            return False
    
    def fail_task(self, task_id: str, error_message: str) -> bool:
        """标记任务失败
        
        Args:
            task_id: 任务ID
            error_message: 错误信息
            
        Returns:
            失败标记成功返回True
        """
        try:
            with self.redis.pipeline() as pipe:
                pipe.multi()
                
                # 从监控队列移除
                pipe.zrem(self.QUEUE_MONITORING, task_id)
                
                # 更新任务状态
                updates = {
                    "status": "failed",
                    "error_message": error_message,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                pipe.hmset(f"{self.KEY_TASK}{task_id}", updates)
                
                pipe.execute()
            
            logger.warning(f"任务已失败: {task_id} - {error_message}")
            return True
            
        except Exception as e:
            logger.error(f"标记任务失败失败: {e}")
            return False
    
    def get_task(self, task_id: str) -> Optional[VideoTask]:
        """获取单个任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象或None
        """
        try:
            task_data = self.redis.hgetall(f"{self.KEY_TASK}{task_id}")
            if task_data:
                return VideoTask.from_dict(task_data)
            return None
            
        except Exception as e:
            logger.error(f"获取任务失败: {e}")
            return None
    
    def get_queue_stats(self) -> Dict[str, int]:
        """获取队列统计信息
        
        Returns:
            统计信息字典
        """
        try:
            return {
                "pending": self.redis.zcard(self.QUEUE_PENDING),
                "monitoring": self.redis.zcard(self.QUEUE_MONITORING)
            }
            
        except Exception as e:
            logger.error(f"获取队列统计失败: {e}")
            return {"pending": 0, "monitoring": 0}


@dataclass
class ImageTask:
    """图片存储任务数据模型"""
    task_id: str
    request_id: str  # API请求ID
    prompt: str
    model: str
    image_urls: List[str]  # 图片URL列表
    status: str = "pending"  # pending, completed, failed
    created_at: str = ""
    updated_at: str = ""
    minio_urls: Optional[List[str]] = None  # MinIO存储URL列表
    generation_params: Optional[Dict[str, Any]] = None  # 生成参数
    error_message: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于Redis存储"""
        data = asdict(self)
        # 处理JSON序列化
        if self.image_urls:
            data['image_urls'] = json.dumps(self.image_urls)
        if self.minio_urls:
            data['minio_urls'] = json.dumps(self.minio_urls)
        if self.generation_params:
            data['generation_params'] = json.dumps(self.generation_params)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImageTask':
        """从字典创建实例"""
        processed_data = data.copy()
        
        # 反序列化JSON字段
        for field in ['image_urls', 'minio_urls']:
            if field in processed_data and isinstance(processed_data[field], str):
                try:
                    processed_data[field] = json.loads(processed_data[field]) if processed_data[field] else []
                except json.JSONDecodeError:
                    processed_data[field] = []
        
        if 'generation_params' in processed_data and isinstance(processed_data['generation_params'], str):
            try:
                processed_data['generation_params'] = json.loads(processed_data['generation_params']) if processed_data['generation_params'] else {}
            except json.JSONDecodeError:
                processed_data['generation_params'] = {}
        
        return cls(**processed_data)


# 全局实例
simple_task_queue = SimpleTaskQueue()