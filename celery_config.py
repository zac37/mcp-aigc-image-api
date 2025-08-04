#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Celery配置文件
"""

from celery import Celery
from core.simple_config import settings

# 创建Celery应用
app = Celery('video_tasks')

# 配置Redis作为broker和backend
app.conf.update(
    # Redis配置 - 修复：与SimpleTaskQueue使用相同的数据库
    broker_url=f'redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}',
    result_backend=f'redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}',
    
    # 任务配置
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    result_expires=3600,  # 结果保存1小时
    
    # Worker配置
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=50,
    
    # 🎯 方案一：简化架构 - 移除任务路由，使用单一默认队列
    # 所有任务自动路由到 'celery' 默认队列，降低配置复杂度
    # task_routes={},  # 已移除：原三队列架构路由配置
    
    # 重试配置
    task_default_retry_delay=60,  # 默认重试延迟60秒
    task_max_retries=3,  # 最大重试3次
    
    # 定期任务配置
    beat_schedule={
        'monitor-video-tasks': {
            'task': 'celery_tasks.start_video_monitoring',
            'schedule': 60.0,  # 每60秒监控一次
        },
    },
    timezone='UTC',
)

# 自动发现任务 - 修复模块导入问题
# app.autodiscover_tasks(['celery_tasks'])  # 旧配置导致ModuleNotFoundError
# 直接导入任务模块
import celery_tasks

if __name__ == '__main__':
    app.start()