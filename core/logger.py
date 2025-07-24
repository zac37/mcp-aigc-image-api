#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志管理模块

提供统一的日志配置和管理功能
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import settings

# 创建日志目录
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# 日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器（仅用于控制台输出）"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record):
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        return super().format(record)

def setup_logger(
    name: str,
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志器名称
        level: 日志级别
        log_file: 日志文件名
        max_bytes: 日志文件最大大小
        backup_count: 备份文件数量
    
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 设置日志级别
    if level is None:
        level = settings.server.log_level.upper()
    
    logger.setLevel(getattr(logging, level, logging.INFO))
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # 使用彩色格式化器
    console_formatter = ColoredFormatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        file_path = LOG_DIR / log_file
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 文件使用普通格式化器
        file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    获取日志记录器的便捷函数
    
    Args:
        name: 日志器名称
        log_file: 日志文件名（可选）
    
    Returns:
        配置好的日志记录器
    """
    if log_file is None:
        # 根据名称自动生成日志文件名
        safe_name = name.replace(".", "_").replace(" ", "_")
        log_file = f"{safe_name}.log"
    
    return setup_logger(name, log_file=log_file)

# 预定义的日志记录器
def get_main_logger() -> logging.Logger:
    """获取主应用日志记录器"""
    return get_logger("images_api.main", "main.log")

def get_api_logger() -> logging.Logger:
    """获取API日志记录器"""
    return get_logger("images_api.api", "api.log")

def get_mcp_logger() -> logging.Logger:
    """获取MCP日志记录器"""
    return get_logger("images_api.mcp", "mcp.log")

def get_images_client_logger() -> logging.Logger:
    """获取Images客户端日志记录器"""
    return get_logger("images_api.client", "images_client.log")

# 请求日志中间件使用的日志记录器
def get_access_logger() -> logging.Logger:
    """获取访问日志记录器"""
    logger = logging.getLogger("images_api.access")
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # 访问日志使用时间分割
        access_log_path = LOG_DIR / "access.log"
        handler = TimedRotatingFileHandler(
            access_log_path,
            when="midnight",
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        
        # 访问日志格式
        formatter = logging.Formatter(
            "%(asctime)s - %(message)s",
            DATE_FORMAT
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def get_storage_logger() -> logging.Logger:
    """获取存储日志记录器"""
    return get_logger("images_api.storage", "storage.log")

# 错误追踪日志
def log_exception(logger: logging.Logger, e: Exception, context: str = ""):
    """
    记录异常信息
    
    Args:
        logger: 日志记录器
        e: 异常对象
        context: 上下文信息
    """
    error_msg = f"{context}: {str(e)}" if context else str(e)
    logger.exception(error_msg)

# 性能监控日志
def log_performance(logger: logging.Logger, operation: str, duration: float, **kwargs):
    """
    记录性能信息
    
    Args:
        logger: 日志记录器
        operation: 操作名称
        duration: 执行时间（秒）
        **kwargs: 额外的性能指标
    """
    metrics = " ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.info(f"PERF {operation} duration={duration:.3f}s {metrics}")