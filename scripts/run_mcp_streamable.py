#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
运行 Images API MCP 服务 (Enhanced Implementation)

使用增强的ImagesMCPServer实现，兼容Python 3.9+，基于MCP调试指南的最佳实践
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import settings
from core.logger import get_mcp_logger

logger = get_mcp_logger()

def main():
    """主函数：启动Images API MCP服务"""
    try:
        logger.info("Starting Images API MCP Service...")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Service will run on {settings.mcp.host}:{settings.mcp.port}")
        
        # 导入并运行我们的FastMCP服务
        from routers.mcp.main import main as mcp_main
        mcp_main()
        
    except Exception as e:
        logger.error(f"Failed to start MCP service: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()