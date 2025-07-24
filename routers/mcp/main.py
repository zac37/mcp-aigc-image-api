#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Images API MCP 服务主模块

基于简化MCP实现，兼容Python 3.9，参考example中的成功模式
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from core.config import settings
from core.logger import get_mcp_logger
from .simple_mcp_server import SimpleMCPServer
from .images_tools import (
    create_gpt_image_tool,
    create_recraft_image_tool,
    create_seedream_image_tool,
    create_seededit_image_tool,
    create_flux_image_tool,
    create_stable_diffusion_image_tool,
    create_hailuo_image_tool,
    create_doubao_image_tool,
    upload_image_file_tool
)

# 配置日志
logger = get_mcp_logger()

# =============================================================================
# MCP 服务器配置
# =============================================================================

class ImagesMCPServer(SimpleMCPServer):
    """Images API MCP 服务器 - 扩展版本"""
    
    def __init__(self):
        super().__init__()
        
        # 注册资源和提示
        self._register_resources()
        self._register_prompts()
        
        # 设置工具函数映射
        self._setup_tool_functions()
        
        logger.info("✅ Images API MCP服务初始化完成")
        logger.info(f"   📊 工具数量: {len(self.tools)}")
        logger.info(f"   🛠️ 工具函数: {len(self._tool_functions)}")
        logger.info(f"   📋 资源数量: {len(getattr(self, 'resources', {}))}")
        logger.info(f"   💡 提示数量: {len(getattr(self, 'prompts', {}))}")
    
    def _setup_tool_functions(self):
        """设置工具函数映射"""
        self._tool_functions = {
            'create_gpt_image': create_gpt_image_tool,
            'create_recraft_image': create_recraft_image_tool,
            'create_seedream_image': create_seedream_image_tool,
            'create_seededit_image': create_seededit_image_tool,
            'create_flux_image': create_flux_image_tool,
            'create_stable_diffusion_image': create_stable_diffusion_image_tool,
            'create_hailuo_image': create_hailuo_image_tool,
            'create_doubao_image': create_doubao_image_tool,
            'upload_image_file': upload_image_file_tool
        }
        
        logger.info(f"📝 工具函数映射设置完成: {list(self._tool_functions.keys())}")
    
    def _register_resources(self):
        """注册MCP资源"""
        self.resources = {
            "images://config": {
                "name": "Images API配置",
                "description": "Images API MCP服务配置信息",
                "content": {
                    "name": "Images API",
                    "version": "1.0.0",
                    "description": "多种图像生成AI API代理服务的MCP工具集合",
                    "modules": [
                        "gpt_image", "recraft_image", "seedream_image", 
                        "seededit_image", "flux_image", "stable_diffusion",
                        "hailuo_image", "doubao_image"
                    ],
                    "supported_models": [
                        "GPT (DALL-E 2/3)", "Recraft", "即梦3.0", "即梦垫图",
                        "FLUX", "Stable Diffusion", "海螺AI", "豆包"
                    ],
                    "api_key_managed": True,
                    "python_version": "3.9+",
                    "features": [
                        "文生图", "图像编辑", "虚拟换衣", "多模型支持"
                    ]
                }
            }
        }
    
    def _register_prompts(self):
        """注册MCP提示"""
        self.prompts = {
            "images_usage_guide": {
                "name": "Images API使用指南",
                "description": "Images API MCP工具使用指南",
                "content": """
# Images API 使用指南

## 功能概览
Images API提供多种AI图像生成功能：

### 1. GPT图像生成 (DALL-E)
使用OpenAI DALL-E模型生成高质量图像
- **工具**: create_gpt_image
- **参数**: prompt（必需）, model, n, size, quality, style
- **模型**: dall-e-3（推荐）, dall-e-2
- **尺寸**: 1024x1024, 1792x1024, 1024x1792等

### 2. Recraft图像生成
专业的图像创作工具，支持多种艺术风格
- **工具**: create_recraft_image
- **参数**: prompt（必需）, style, size, image_format
- **风格**: realistic, artistic, vector等
- **格式**: png, jpg

### 3. 即梦3.0图像生成
先进的图像生成技术，支持精确控制
- **工具**: create_seedream_image
- **参数**: prompt（必需）, aspect_ratio, negative_prompt, cfg_scale, seed
- **宽高比**: 1:1, 16:9, 9:16, 4:3, 3:4
- **CFG范围**: 1.0-20.0，推荐7.5

### 4. 即梦垫图编辑
基于现有图像的智能编辑功能
- **工具**: create_seededit_image
- **参数**: image_url（必需）, prompt（必需）, strength, seed
- **强度范围**: 0.0-1.0，推荐0.8
- **说明**: 图片URL必须是有效的HTTP/HTTPS链接

### 5. FLUX图像生成
高质量的开源图像生成模型
- **工具**: create_flux_image
- **参数**: prompt（必需）, aspect_ratio, steps, guidance, seed
- **推理步数**: 1-50，推荐20
- **引导强度**: 1.0-20.0，推荐7.5

### 6. Stable Diffusion
经典的开源图像生成模型
- **工具**: create_stable_diffusion_image
- **参数**: prompt（必需）, size, n
- **尺寸比例**: 1:1, 2:3, 3:2, 3:4, 4:3, 9:16, 16:9
- **数量**: 1-10张

### 7. 海螺AI图像生成
海螺AI的图像生成服务
- **工具**: create_hailuo_image
- **参数**: prompt（必需）, size, quality, seed

### 8. 豆包图像生成
字节跳动的图像生成服务
- **工具**: create_doubao_image
- **参数**: prompt（必需）, size, guidance_scale, watermark
- **指导强度**: 1-10，推荐3

## 重要提示
- ✅ API密钥已在服务端配置，无需手动传递
- 🎯 所有任务都会返回JSON格式结果
- 📊 包含图像URL、任务信息等完整数据
- 🔄 支持同步调用，无需轮询状态
- 📝 详细的错误信息和异常处理

## 最佳实践
1. **提示词优化**: 详细描述想要的结果，包含风格、情感、环境
2. **参数调优**: 根据需求调整各种控制参数
3. **模型选择**: 根据用途选择最适合的生成模型
4. **错误处理**: 检查返回结果中的错误信息
5. **图片链接**: 确保输入的图片URL可访问

## 技术架构
- 🏗️ 基于FastAPI的RESTful服务
- 🔧 MCP协议兼容，支持AI Agent调用
- 🚀 异步处理，高性能并发
- 🛡️ 完整的错误处理和日志记录
- 📦 统一的响应格式和状态管理
"""
            }
        }
    
    async def get_resource(self, resource_uri: str) -> dict:
        """获取资源内容"""
        if resource_uri in self.resources:
            return self.resources[resource_uri]["content"]
        raise ValueError(f"Resource not found: {resource_uri}")
    
    async def get_prompt(self, prompt_name: str) -> str:
        """获取提示内容"""
        if prompt_name in self.prompts:
            return self.prompts[prompt_name]["content"]
        raise ValueError(f"Prompt not found: {prompt_name}")

# =============================================================================
# 创建全局MCP服务器实例
# =============================================================================

# 创建MCP服务器实例
mcp_server = ImagesMCPServer()

# 添加所有工具（模仿FastMCP的add_tool方式）
logger.info("开始注册Images API MCP工具模块...")

# 注册工具函数映射
# tool_functions = {
#     'create_gpt_image': create_gpt_image_tool,
#     'create_recraft_image': create_recraft_image_tool,
#     'create_seedream_image': create_seedream_image_tool,
#     'create_seededit_image': create_seededit_image_tool,
#     'create_flux_image': create_flux_image_tool,
#     'create_stable_diffusion_image': create_stable_diffusion_image_tool,
#     'create_virtual_try_on': create_virtual_try_on_tool,
#     'create_hailuo_image': create_hailuo_image_tool,
#     'create_doubao_image': create_doubao_image_tool
# }

# 更新服务器的工具函数映射
# mcp_server._tool_functions = tool_functions

logger.info("✅ Images API MCP工具模块注册完成")

# =============================================================================
# MCP 服务运行
# =============================================================================

async def main():
    """运行 MCP 服务"""
    logger.info("Starting Images API MCP service...")
    logger.info(f"MCP service will run on {settings.mcp.host}:{settings.mcp.port}")
    logger.info(f"Transport: streamable-http (simplified)")
    logger.info(f"Python version: 3.9+ compatible")
    
    try:
        # 导入run_simple_mcp_server函数
        from .simple_mcp_server import run_simple_mcp_server
        
        # 使用我们的ImagesMCPServer实例运行服务
        await run_simple_mcp_server(
            server_instance=mcp_server,
            host=settings.mcp.host,
            port=settings.mcp.port
        )
    except Exception as e:
        logger.error(f"Failed to start MCP service: {e}")
        raise

# 导出app变量供外部使用 - 关键！
app = mcp_server

if __name__ == "__main__":
    asyncio.run(main())