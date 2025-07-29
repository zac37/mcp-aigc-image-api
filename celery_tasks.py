#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Celery任务定义 - 解耦的视频任务监控器
"""

import time
import asyncio
import uuid
import requests
import io
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from celery import Task
from celery.exceptions import Retry

from celery_config import app
from core.logger import get_logger
from core.simple_task_queue import simple_task_queue, VideoTask, ImageTask
from core.minio_client import get_minio_client
# 不再直接导入veo3客户端，改为调用FastAPI接口

logger = get_logger(__name__)

def make_sync_api_call(url: str, method: str = "GET", data: Optional[dict] = None, timeout: int = 300) -> dict:
    """同步HTTP API调用，避免事件循环问题"""
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'CeleryWorker/1.0'
    }
    
    try:
        if method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=timeout)
        else:
            response = requests.get(url, headers=headers, timeout=timeout)
            
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP请求失败: {e}")
        raise Exception(f"API调用失败: {str(e)}")

def download_file_sync(url: str, timeout: int = 300) -> bytes:
    """同步下载文件"""
    try:
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        logger.error(f"文件下载失败: {e}")
        raise Exception(f"下载失败: {str(e)}")

def upload_to_minio_sync(content: bytes, path: str, content_type: str = "video/mp4") -> str:
    """同步上传到MinIO并获取访问URL"""
    try:
        # 获取MinIO客户端
        minio_client = get_minio_client()
        
        # 同步上传 - 直接使用MinIO的同步方法
        from minio import Minio
        from minio.error import S3Error
        import os
        
        # 创建同步MinIO客户端
        sync_client = Minio(
            endpoint=os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
            access_key=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
            secret_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin123'),
            secure=False
        )
        
        bucket = os.getenv('MINIO_BUCKET', 'images')
        
        # 上传文件
        sync_client.put_object(
            bucket,
            path,
            io.BytesIO(content),
            length=len(content),
            content_type=content_type
        )
        
        logger.info(f"文件上传到MinIO成功: {path}")
        
        # 生成预签名URL
        from urllib.parse import urljoin
        import urllib.parse
        
        # 简单的URL生成 - 在生产环境中应该使用presigned URL
        minio_endpoint = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
        access_url = f"http://{minio_endpoint}/{bucket}/{path}"
        
        return access_url
        
    except Exception as e:
        logger.error(f"MinIO上传失败: {e}")
        raise Exception(f"存储失败: {str(e)}")


class CallbackTask(Task):
    """带状态回调的Celery任务基类"""
    
    def on_success(self, retval, task_id, args, kwargs):
        """任务成功完成时的回调"""
        logger.info(f"Task {task_id} completed successfully")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败时的回调"""
        logger.error(f"Task {task_id} failed: {exc}")
    
    def update_progress(self, current: int, total: int = 100, status: str = "PROGRESS"):
        """更新任务进度"""
        self.update_state(
            state=status,
            meta={
                'progress': current,
                'total': total,
                'percentage': int((current / total) * 100)
            }
        )


@app.task(bind=True, base=CallbackTask)
def monitor_video_tasks(self) -> Dict[str, Any]:
    """
    视频任务监控器 - 轮询简单队列中的任务并处理
    
    只负责监控，不创建任务，保持Celery的轻量和独立
    """
    celery_task_id = self.request.id
    start_time = time.time()
    logger.info(f"[{celery_task_id}] 开始监控视频任务...")
    
    processed_count = 0
    
    try:
        # 1. 获取待处理的任务
        pending_tasks = simple_task_queue.get_pending_tasks(limit=5)
        
        # 2. 获取正在监控的任务
        monitoring_tasks = simple_task_queue.get_monitoring_tasks(limit=20)
        
        logger.info(f"[{celery_task_id}] 发现 {len(pending_tasks)} 个待处理任务，{len(monitoring_tasks)} 个监控中任务")
        
        # 3. 将待处理任务移到监控队列
        for task in pending_tasks:
            try:
                success = simple_task_queue.move_to_monitoring(task.task_id)
                if success:
                    logger.info(f"[{celery_task_id}] 任务移到监控队列: {task.task_id}")
                    processed_count += 1
            except Exception as e:
                logger.error(f"[{celery_task_id}] 移动任务失败: {task.task_id} - {e}")
        
        # 4. 检查监控中任务的状态
        for task in monitoring_tasks:
            try:
                success = _check_and_process_task(task)
                if success:
                    processed_count += 1
            except Exception as e:
                logger.error(f"[{celery_task_id}] 处理监控任务失败: {task.task_id} - {e}")
        
        processing_time = time.time() - start_time
        logger.info(f"[{celery_task_id}] 监控完成，处理了 {processed_count} 个任务，耗时: {processing_time:.1f}秒")
        
        return {
            "celery_task_id": celery_task_id,
            "status": "completed",
            "processed_count": processed_count,
            "pending_tasks": len(pending_tasks),
            "monitoring_tasks": len(monitoring_tasks),
            "processing_time_seconds": round(processing_time, 1),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"[{celery_task_id}] 监控任务失败: {exc}")
        return {
            "celery_task_id": celery_task_id,
            "status": "failed",
            "error": str(exc),
            "processed_count": processed_count,
            "timestamp": datetime.now().isoformat()
        }
    
def _check_and_process_task(task: VideoTask) -> bool:
    """检查并处理单个视频任务
    
    Args:
        task: 视频任务对象
        
    Returns:
        处理成功返回True
    """
    try:
        # 如果任务还没有外部ID，说明任务创建有问题，标记失败
        if not task.external_task_id:
            logger.error(f"任务缺少外部ID: {task.task_id}")
            simple_task_queue.fail_task(task.task_id, "任务缺少外部ID")
            return False
        
        # 调用FastAPI的状态查询接口
        api_url = f"http://localhost:5512/api/veo3/official/status/{task.external_task_id}"
        
        try:
            response = make_sync_api_call(api_url, method="GET")
            
            if response.get('success'):
                data = response.get('data', {})
                status = data.get('status', 'unknown')
                logger.info(f"外部任务状态: {task.external_task_id} -> {status}")
                
                # 根据状态更新本地任务
                if status == 'completed':
                    # 任务完成，获取视频URL
                    # 优先使用public_url，其次使用video_url
                    video_url = data.get('public_url') or data.get('video_url')
                    gcs_uri = data.get('gcs_uri')
                    
                    # 如果没有public_url，尝试从嵌套的data中获取
                    if not video_url:
                        task_data = data.get('data', {})
                        if task_data and isinstance(task_data, dict):
                            videos = task_data.get('videos', [])
                            if videos and len(videos) > 0:
                                video_info = videos[0]
                                gcs_uri = video_info.get('gcsUri')
                                # 如果只有GCS URI，跳过下载
                                if gcs_uri and gcs_uri.startswith('gs://'):
                                    logger.warning(f"只有GCS URI，无法下载，任务标记为完成但不上传到MinIO: {gcs_uri}")
                                    simple_task_queue.complete_task(task.task_id, gcs_uri, None)
                                    return True
                    
                    logger.info(f"获取到视频URL: {video_url}, GCS URI: {gcs_uri}")
                    
                    if video_url:
                        # 检查是否为可下载的HTTP URL
                        if video_url.startswith(('http://', 'https://')):
                            # 下载并上传到MinIO
                            logger.info(f"准备下载视频: {video_url}")
                            minio_url = _download_and_upload_video(task, video_url)
                            simple_task_queue.complete_task(task.task_id, gcs_uri or video_url, minio_url)
                            logger.info(f"任务完成: {task.task_id}")
                            return True
                        else:
                            # 非HTTP URL，标记完成但不下载
                            logger.warning(f"视频URL不是HTTP格式，跳过下载: {video_url}")
                            simple_task_queue.complete_task(task.task_id, video_url, None)
                            return True
                    else:
                        logger.warning(f"任务完成但未获取到视频URL")
                        simple_task_queue.fail_task(task.task_id, "未获取到视频URL")
                        return False
                        
                elif status == 'failed':
                    # 任务失败
                    error_msg = data.get('error') or "外部任务失败"
                    simple_task_queue.fail_task(task.task_id, error_msg)
                    logger.warning(f"任务失败: {task.task_id} - {error_msg}")
                    return False
                    
                else:
                    # 任务还在进行中（submitted, running等）
                    simple_task_queue.update_task(task.task_id, external_status=status)
                    logger.debug(f"任务进行中: {task.task_id} - {status}")
                    return True
            else:
                # API调用失败
                error_msg = response.get('error') or response.get('detail') or "API调用失败"
                logger.error(f"API调用失败: {task.task_id} - {error_msg}")
                # 不立即标记为失败，可能是暂时的网络问题
                return False
                
        except Exception as api_error:
            logger.error(f"调用状态查询API失败: {task.task_id} - {api_error}")
            # 不立即标记为失败，可能是暂时的网络问题
            return False
            
    except Exception as e:
        logger.error(f"检查任务状态失败: {task.task_id} - {e}")
        return False
    
def _download_and_upload_video(task: VideoTask, video_url: str) -> Optional[str]:
    """下载视频并上传到MinIO
    
    Args:
        task: 任务对象
        video_url: 视频URL
        
    Returns:
        MinIO访问URL或None
    """
    try:
        logger.info(f"开始下载视频: {task.task_id} - {video_url}")
        
        # 下载视频
        video_content = download_file_sync(video_url, timeout=300)
        video_size_mb = len(video_content) / (1024 * 1024)
        logger.info(f"视频下载完成: {task.task_id}, 大小: {video_size_mb:.1f}MB")
        
        # 生成文件名和路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"veo3_{task.task_id}_{timestamp}.mp4"
        minio_path = f"videos/{datetime.now().strftime('%Y/%m/%d')}/{filename}"
        
        # 上传到MinIO
        logger.info(f"开始上传到MinIO: {task.task_id} - {minio_path}")
        minio_url = upload_to_minio_sync(video_content, minio_path, "video/mp4")
        
        logger.info(f"文件上传完成: {task.task_id} - {minio_url}")
        return minio_url
        
    except Exception as e:
        logger.error(f"下载上传视频失败: {task.task_id} - {e}")
        return None


# 定期任务启动器
@app.task
def start_video_monitoring():
    """启动视频任务监控 - 定期调用"""
    result = monitor_video_tasks.delay()
    logger.info(f"启动视频监控任务: {result.id}")
    return {"monitor_task_id": result.id, "status": "started"}




# 工具函数
def get_task_info(task_id: str) -> Dict[str, Any]:
    """
    获取任务信息
    
    Args:
        task_id: Celery任务ID
        
    Returns:
        任务状态和结果信息
    """
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id, app=app)
    
    # 基础状态信息
    info = {
        "task_id": task_id,
        "status": result.status,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else None,
        "failed": result.failed() if result.ready() else None,
    }
    
    # 如果任务完成，添加结果
    if result.ready():
        try:
            info["result"] = result.result
        except Exception as e:
            info["error"] = str(e)
    
    # 如果有进度信息，添加进度
    elif result.state == 'PROGRESS' and result.info:
        info.update(result.info)
    
    return info


# =============================================================================
# 图片存储任务
# =============================================================================

@app.task(bind=True, base=CallbackTask)
def store_images_to_minio(self, image_task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    将图片存储到MinIO的Celery任务
    
    Args:
        image_task_data: ImageTask的字典数据
        
    Returns:
        任务执行结果
    """
    celery_task_id = self.request.id
    
    try:
        # 从字典重构ImageTask对象
        image_task = ImageTask.from_dict(image_task_data)
        task_id = image_task.task_id
        
        logger.info(f"[{celery_task_id}] 开始存储图片任务: {task_id}")
        logger.info(f"[{celery_task_id}] 图片数量: {len(image_task.image_urls)}")
        
        minio_urls = []
        
        # 处理每张图片
        for i, image_url in enumerate(image_task.image_urls):
            try:
                logger.info(f"[{celery_task_id}] 下载图片 {i+1}/{len(image_task.image_urls)}: {image_url}")
                
                # 下载图片
                image_content = download_file_sync(image_url, timeout=60)
                image_size_mb = len(image_content) / (1024 * 1024)
                logger.info(f"[{celery_task_id}] 图片下载完成，大小: {image_size_mb:.1f}MB")
                
                # 生成存储路径
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{image_task.model}_{task_id}_{i+1}_{timestamp}.jpg"
                minio_path = f"images/{datetime.now().strftime('%Y/%m/%d')}/{filename}"
                
                # 上传到MinIO
                logger.info(f"[{celery_task_id}] 上传到MinIO: {minio_path}")
                minio_url = upload_to_minio_sync(image_content, minio_path, "image/jpeg")
                minio_urls.append(minio_url)
                
                logger.info(f"[{celery_task_id}] 图片 {i+1} 存储完成: {minio_url}")
                
            except Exception as e:
                logger.error(f"[{celery_task_id}] 处理图片 {i+1} 失败: {e}")
                # 继续处理其他图片，不要因为一张图片失败就停止整个任务
                minio_urls.append(None)
        
        # 更新任务状态（这里可以扩展一个ImageTaskQueue来管理）
        success_count = len([url for url in minio_urls if url])
        
        logger.info(f"[{celery_task_id}] 图片存储任务完成: {task_id}")
        logger.info(f"[{celery_task_id}] 成功存储: {success_count}/{len(image_task.image_urls)} 张图片")
        
        return {
            "celery_task_id": celery_task_id,
            "image_task_id": task_id,
            "status": "completed",
            "total_images": len(image_task.image_urls),
            "success_count": success_count,
            "minio_urls": minio_urls,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"[{celery_task_id}] 图片存储任务失败: {exc}")
        return {
            "celery_task_id": celery_task_id,
            "status": "failed",
            "error": str(exc),
            "timestamp": datetime.now().isoformat()
        }


def submit_image_storage_task(
    request_id: str,
    prompt: str,
    model: str,
    image_urls: List[str],
    generation_params: Optional[Dict[str, Any]] = None
) -> str:
    """
    提交图片存储任务到Celery队列
    
    Args:
        request_id: API请求ID
        prompt: 生成提示词
        model: 使用的模型
        image_urls: 图片URL列表
        generation_params: 生成参数
        
    Returns:
        Celery任务ID
    """
    # 创建ImageTask
    image_task = ImageTask(
        task_id=str(uuid.uuid4()),
        request_id=request_id,
        prompt=prompt,
        model=model,
        image_urls=image_urls,
        generation_params=generation_params or {}
    )
    
    # 提交到Celery
    result = store_images_to_minio.delay(image_task.to_dict())
    
    logger.info(f"图片存储任务已提交: {image_task.task_id} -> Celery: {result.id}")
    
    return result.id


if __name__ == "__main__":
    # 测试用例
    print("Celery tasks module loaded successfully")