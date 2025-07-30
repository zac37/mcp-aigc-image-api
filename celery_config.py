#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Celery配置文件
"""

from celery import Celery
from core.config import settings

# 创建Celery应用
app = Celery('video_tasks')

# 配置Redis作为broker和backend
app.conf.update(
    # Redis配置
    broker_url=f'redis://{settings.redis.host}:{settings.redis.port}/1',
    result_backend=f'redis://{settings.redis.host}:{settings.redis.port}/2',
    
    # 任务配置
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    result_expires=3600,  # 结果保存1小时
    
    # Worker配置
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=50,
    
    # 任务路由
    task_routes={
        'celery_tasks.monitor_video_tasks': {'queue': 'video_monitor_queue'},
        'celery_tasks.start_video_monitoring': {'queue': 'video_monitor_queue'},
        'celery_tasks.store_images_to_minio': {'queue': 'image_queue'},
    },
    
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

# 自动发现任务
app.autodiscover_tasks(['celery_tasks'])

if __name__ == '__main__':
    app.start()