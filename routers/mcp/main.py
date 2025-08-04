#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Images API MCP 服务主模块

使用fastmcp库实现MCP协议
"""

import asyncio
from fastmcp import FastMCP
from core.simple_config import settings
from core.logger import get_mcp_logger

# 导入所有MCP工具函数
from .images_tools import (
    create_gpt_image_tool,
    create_gpt_image_edit_tool,
    create_recraft_image_tool,
    create_seedream_image_tool,
    create_seededit_image_tool,
    create_flux_image_tool,
    create_stable_diffusion_image_tool,
    create_hailuo_image_tool,
    create_doubao_image_tool,
    create_veo3_video_tool,
    get_veo3_task_tool,
    create_veo3_official_video_tool,
    check_veo3_official_status_tool,
    upload_image_file_tool
)

# 配置日志
logger = get_mcp_logger()

# 创建MCP应用
mcp = FastMCP("Images API MCP Service")

# =============================================================================
# 注册MCP工具
# =============================================================================

# GPT图像生成
mcp.tool()(create_gpt_image_tool)
mcp.tool()(create_gpt_image_edit_tool)

# Recraft图像生成
mcp.tool()(create_recraft_image_tool)

# 即梦系列
mcp.tool()(create_seedream_image_tool)
mcp.tool()(create_seededit_image_tool)

# FLUX系列
mcp.tool()(create_flux_image_tool)

# 其他图像模型
mcp.tool()(create_stable_diffusion_image_tool)
mcp.tool()(create_hailuo_image_tool)
mcp.tool()(create_doubao_image_tool)

# Veo3视频生成
mcp.tool()(create_veo3_video_tool)
mcp.tool()(get_veo3_task_tool)
mcp.tool()(create_veo3_official_video_tool)
mcp.tool()(check_veo3_official_status_tool)

# 文件上传工具
mcp.tool()(upload_image_file_tool)

def main():
    """运行 MCP 服务"""
    logger.info("Starting Images API MCP Service...")
    logger.info(f"Service will run on {settings.mcp_host}:{settings.mcp_port}")
    
    try:
        mcp.run(
            transport="streamable-http",
            host=settings.mcp_host,
            port=settings.mcp_port
        )
    except KeyboardInterrupt:
        logger.info("MCP service stopped by user")
    except Exception as e:
        logger.error(f"Failed to start MCP service: {e}")
        raise

if __name__ == "__main__":
    main()