#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MinIO 对象存储客户端

提供文件上传、下载、删除和URL生成功能
"""

import asyncio
import uuid
from datetime import timedelta, datetime
from typing import Optional, Dict, Any, BinaryIO, Union, List
from pathlib import Path
import mimetypes
import hashlib
import io

from minio import Minio
from minio.error import S3Error, InvalidResponseError
from fastapi import HTTPException, UploadFile

from core.config import settings
from core.logger import get_storage_logger, log_exception

logger = get_storage_logger()

class MinIOError(Exception):
    """MinIO操作异常"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class MinIOClient:
    """MinIO客户端封装类"""
    
    def __init__(self):
        """初始化MinIO客户端"""
        self.client = None
        self.bucket_name = settings.minio.bucket_name
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化MinIO客户端连接"""
        try:
            self.client = Minio(
                endpoint=settings.minio.endpoint,
                access_key=settings.minio.access_key,
                secret_key=settings.minio.secret_key,
                secure=settings.minio.secure,
                region=settings.minio.region
            )
            logger.info(f"MinIO client initialized successfully: {settings.minio.endpoint}")
            
            # 跳过存储桶检查，假设存储桶已存在
            logger.info(f"MinIO client initialized, assuming bucket exists: {self.bucket_name}")
            
        except Exception as e:
            log_exception(logger, e, "Failed to initialize MinIO client")
            raise MinIOError(f"MinIO initialization failed: {str(e)}")
    
    def _ensure_bucket_exists(self):
        """确保存储桶存在"""
        try:
            # 首先检查存储桶是否存在
            bucket_exists = self.client.bucket_exists(self.bucket_name)
            if bucket_exists:
                logger.info(f"Bucket already exists: {self.bucket_name}")
                return
            
            # 如果不存在，尝试创建
            try:
                self.client.make_bucket(self.bucket_name, location=settings.minio.region)
                logger.info(f"Created bucket: {self.bucket_name}")
            except Exception as create_error:
                # 再次检查是否存在（可能是并发创建）
                if self.client.bucket_exists(self.bucket_name):
                    logger.info(f"Bucket was created by another process: {self.bucket_name}")
                    return
                else:
                    raise create_error
                    
        except Exception as e:
            # 如果检查存在性和创建都失败，但存储桶可能实际存在，尝试继续
            try:
                # 最后一次检查
                if self.client.bucket_exists(self.bucket_name):
                    logger.warning(f"Bucket exists despite error during creation check: {self.bucket_name}")
                    return
            except:
                pass
            
            log_exception(logger, e, f"Failed to ensure bucket exists: {self.bucket_name}")
            raise MinIOError(f"Bucket creation failed: {str(e)}")
    
    def _generate_object_name(self, filename: str, folder: str = "uploads", content_type: str = "manual_uploads") -> str:
        """生成对象存储路径
        
        Args:
            filename: 文件名
            folder: 存储文件夹 (已废弃，保留兼容性)
            content_type: 内容类型 ('ai_generated' 或 'manual_uploads')
            
        Returns:
            统一格式的对象路径: {content_type}/{type}/{YYYY/MM/DD}/{filename}
        """
        # 获取文件扩展名
        file_suffix = Path(filename).suffix.lower()
        
        # 根据文件扩展名确定类型
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv'}
        
        if file_suffix in image_extensions:
            asset_type = "images"
        elif file_suffix in video_extensions:
            asset_type = "videos"
        else:
            asset_type = "files"
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        new_filename = f"{Path(filename).stem}_{timestamp}_{unique_id}{file_suffix}"
        
        # 构建统一的对象路径: {content_type}/{type}/{YYYY/MM/DD}/{filename}
        date_path = datetime.now().strftime("%Y/%m/%d")
        object_name = f"{content_type}/{asset_type}/{date_path}/{new_filename}"
        
        return object_name
    
    def _get_content_type(self, filename: str) -> str:
        """获取文件MIME类型"""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or 'application/octet-stream'
    
    def _validate_file(self, file: UploadFile, max_size_mb: int = 50) -> None:
        """验证上传文件"""
        # 检查文件名
        if not file.filename:
            raise MinIOError("文件名不能为空", 400)
        
        # 检查文件大小 (通过读取内容检查)
        file.file.seek(0, 2)  # 移动到文件末尾
        file_size = file.file.tell()
        file.file.seek(0)  # 重置到开头
        
        max_size_bytes = max_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            raise MinIOError(f"文件大小超过限制 ({max_size_mb}MB)", 400)
        
        # 检查文件类型 (基于扩展名)
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
        file_suffix = Path(file.filename).suffix.lower()
        if file_suffix not in allowed_extensions:
            raise MinIOError(f"不支持的文件类型: {file_suffix}", 400)
    
    async def upload_file(
        self, 
        file: UploadFile, 
        folder: str = "uploads",
        max_size_mb: int = 50,
        generate_thumbnail: bool = False,
        content_type: str = "manual_uploads"
    ) -> Dict[str, Any]:
        """
        上传文件到MinIO
        
        Args:
            file: FastAPI上传文件对象
            folder: 存储文件夹 (已废弃，保留兼容性)
            max_size_mb: 最大文件大小(MB)
            generate_thumbnail: 是否生成缩略图
            content_type: 内容类型 ('ai_generated' 或 'manual_uploads')
            
        Returns:
            包含文件信息的字典
        """
        try:
            # 验证文件
            self._validate_file(file, max_size_mb)
            
            # 生成对象名称
            object_name = self._generate_object_name(file.filename, folder, content_type)
            
            # 读取文件内容
            file_data = await file.read()
            file_size = len(file_data)
            
            # 计算文件哈希值
            file_hash = hashlib.md5(file_data).hexdigest()
            
            # 获取内容类型
            content_type = self._get_content_type(file.filename)
            
            # 上传文件
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.put_object(
                    bucket_name=self.bucket_name,
                    object_name=object_name,
                    data=io.BytesIO(file_data),
                    length=file_size,
                    content_type=content_type,
                    metadata={
                        'original-filename': file.filename,
                        'upload-time': datetime.now().isoformat(),
                        'file-hash': file_hash
                    }
                )
            )
            
            # 生成访问URL
            file_url = await self.get_presigned_url(object_name)
            
            logger.info(f"File uploaded successfully: {object_name} ({file_size} bytes)")
            
            return {
                'object_name': object_name,
                'original_filename': file.filename,
                'file_size': file_size,
                'content_type': content_type,
                'file_hash': file_hash,
                'file_url': file_url,
                'upload_time': datetime.now().isoformat(),
                'bucket': self.bucket_name
            }
            
        except MinIOError:
            raise
        except Exception as e:
            log_exception(logger, e, f"Failed to upload file: {file.filename}")
            raise MinIOError(f"文件上传失败: {str(e)}")
    
    async def get_presigned_url(
        self, 
        object_name: str, 
        expires_hours: Optional[int] = None
    ) -> str:
        """
        生成预签名URL
        
        Args:
            object_name: 对象名称
            expires_hours: 过期时间(小时)
            
        Returns:
            预签名URL
        """
        try:
            expires_hours = expires_hours or settings.minio.url_expiry_hours
            expires = timedelta(hours=expires_hours)
            
            url = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.presigned_get_object(
                    bucket_name=self.bucket_name,
                    object_name=object_name,
                    expires=expires
                )
            )
            
            return url
            
        except Exception as e:
            log_exception(logger, e, f"Failed to generate presigned URL: {object_name}")
            raise MinIOError(f"生成访问URL失败: {str(e)}")
    
    async def delete_file(self, object_name: str) -> bool:
        """
        删除文件
        
        Args:
            object_name: 对象名称
            
        Returns:
            是否删除成功
        """
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.remove_object(
                    bucket_name=self.bucket_name,
                    object_name=object_name
                )
            )
            
            logger.info(f"File deleted successfully: {object_name}")
            return True
            
        except Exception as e:
            log_exception(logger, e, f"Failed to delete file: {object_name}")
            raise MinIOError(f"文件删除失败: {str(e)}")
    
    async def get_file_info(self, object_name: str) -> Optional[Dict[str, Any]]:
        """
        获取文件信息
        
        Args:
            object_name: 对象名称
            
        Returns:
            文件信息字典或None
        """
        try:
            stat = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.stat_object(
                    bucket_name=self.bucket_name,
                    object_name=object_name
                )
            )
            
            return {
                'object_name': object_name,
                'size': stat.size,
                'content_type': stat.content_type,
                'last_modified': stat.last_modified.isoformat() if stat.last_modified else None,
                'etag': stat.etag,
                'metadata': stat.metadata or {}
            }
            
        except S3Error as e:
            if e.code == 'NoSuchKey':
                return None
            raise MinIOError(f"获取文件信息失败: {str(e)}")
        except Exception as e:
            log_exception(logger, e, f"Failed to get file info: {object_name}")
            raise MinIOError(f"获取文件信息失败: {str(e)}")
    
    async def get_file_stream(self, object_name: str):
        """
        获取文件流数据
        
        Args:
            object_name: 对象名称
            
        Returns:
            文件流数据的异步生成器
        """
        try:
            # 使用线程池执行器获取文件对象
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.get_object(
                    bucket_name=self.bucket_name,
                    object_name=object_name
                )
            )
            
            # 创建异步生成器来流式传输数据
            async def stream_generator():
                try:
                    chunk_size = 8192  # 8KB chunks
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk
                finally:
                    response.close()
                    response.release_conn()
            
            return stream_generator()
            
        except S3Error as e:
            if e.code == 'NoSuchKey':
                raise MinIOError("文件不存在", 404)
            raise MinIOError(f"获取文件流失败: {str(e)}")
        except Exception as e:
            log_exception(logger, e, f"Failed to get file stream: {object_name}")
            raise MinIOError(f"获取文件流失败: {str(e)}")
    
    async def list_files(
        self, 
        prefix: str = "", 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        列出文件
        
        Args:
            prefix: 路径前缀
            limit: 返回数量限制
            
        Returns:
            文件信息列表
        """
        try:
            objects = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: list(self.client.list_objects(
                    bucket_name=self.bucket_name,
                    prefix=prefix,
                    recursive=True
                ))
            )
            
            files = []
            for obj in objects[:limit]:
                files.append({
                    'object_name': obj.object_name,
                    'size': obj.size,
                    'last_modified': obj.last_modified.isoformat() if obj.last_modified else None,
                    'etag': obj.etag
                })
            
            return files
            
        except Exception as e:
            log_exception(logger, e, f"Failed to list files with prefix: {prefix}")
            raise MinIOError(f"列出文件失败: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 检查存储桶是否存在
            bucket_exists = self.client.bucket_exists(self.bucket_name)
            
            return {
                'status': 'healthy' if bucket_exists else 'unhealthy',
                'endpoint': settings.minio.endpoint,
                'bucket': self.bucket_name,
                'bucket_exists': bucket_exists,
                'secure': settings.minio.secure
            }
            
        except Exception as e:
            log_exception(logger, e, "MinIO health check failed")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'endpoint': settings.minio.endpoint,
                'bucket': self.bucket_name
            }

# 全局MinIO客户端实例
_minio_client: Optional[MinIOClient] = None

def get_minio_client() -> MinIOClient:
    """获取MinIO客户端实例"""
    global _minio_client
    if _minio_client is None:
        _minio_client = MinIOClient()
    return _minio_client

async def cleanup_minio_client():
    """清理MinIO客户端"""
    global _minio_client
    if _minio_client:
        logger.info("Cleaning up MinIO client...")
        _minio_client = None