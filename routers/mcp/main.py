#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Images API MCP 服务主模块 - FastMCP版本

基于官方FastMCP实现，支持streamable HTTP协议，Python 3.11+
"""

import asyncio
from core.config import settings
from core.logger import get_mcp_logger
from .fastmcp_server import mcp_app, run_mcp_server

# 配置日志
logger = get_mcp_logger()

# =============================================================================
# MCP 服务运行
# =============================================================================

def main():
    """运行 MCP 服务"""
    logger.info("Starting Images API MCP service with FastMCP...")
    logger.info(f"MCP service will run on {settings.mcp.host}:{settings.mcp.port}")
    logger.info(f"Transport: streamable-http (official FastMCP)")
    logger.info(f"Python version: 3.11+ compatible")
    
    try:
        # 使用FastMCP运行MCP服务
        run_mcp_server()
    except Exception as e:
        logger.error(f"Failed to start MCP service: {e}")
        raise

# 导出app变量供外部使用 - 关键！
app = mcp_app

if __name__ == "__main__":
    asyncio.run(main())