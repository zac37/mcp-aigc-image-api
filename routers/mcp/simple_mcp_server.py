#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简化的MCP服务器实现
Compatible with Python 3.9+, 基于MCP调试指南的最佳实践

提供MCP协议兼容的HTTP服务，不依赖fastmcp包
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from aiohttp import web, WSMsgType
from aiohttp.web import Application, Request, Response, WebSocketResponse
import logging

from core.config import settings
from core.logger import get_mcp_logger

logger = get_mcp_logger()

# =============================================================================
# MCP Protocol Data Models
# =============================================================================

@dataclass
class MCPTool:
    """MCP工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]

@dataclass
class MCPResponse:
    """MCP响应基类"""
    id: Optional[str] = None
    jsonrpc: str = "2.0"

@dataclass
class MCPInitializeResponse(MCPResponse):
    """MCP初始化响应"""
    result: Dict[str, Any] = None

@dataclass
class MCPListToolsResponse(MCPResponse):
    """MCP工具列表响应"""
    result: Dict[str, List[Dict]] = None

@dataclass
class MCPCallToolResponse(MCPResponse):
    """MCP工具调用响应"""
    result: Dict[str, Any] = None

# =============================================================================
# MCP Server Implementation
# =============================================================================

class SimpleMCPServer:
    """简化的MCP服务器实现"""
    
    def __init__(self):
        self.app = web.Application()
        self.tools = self._register_tools()
        self.sessions: Dict[str, Dict] = {}
        self._tool_functions: Dict[str, Any] = {}
        
        # 配置路由
        self.app.router.add_post('/mcp/v1', self.handle_mcp_request)
        self.app.router.add_get('/mcp/v1/health', self.health_check)
        self.app.router.add_get('/mcp/v1/tools', self.list_tools_http)
        self.app.router.add_get('/mcp/v1/info', self.service_info)
        
        logger.info(f"SimpleMCPServer initialized with {len(self.tools)} tools")
    
    def _register_tools(self) -> Dict[str, MCPTool]:
        """注册所有MCP工具"""
        tools = {}
        
        # GPT图像生成工具
        tools['create_gpt_image'] = MCPTool(
            name='create_gpt_image',
            description='创建GPT图像生成任务 - 使用DALL-E模型根据文本描述生成图像',
            parameters={
                'type': 'object',
                'properties': {
                    'prompt': {'type': 'string', 'description': '图像描述提示词，详细描述想要生成的图像内容'},
                    'model': {'type': 'string', 'default': 'dall-e-3', 'description': '模型名称，支持: dall-e-3, dall-e-2'},
                    'n': {'type': 'integer', 'default': 1, 'description': '生成图像数量'},
                    'size': {'type': 'string', 'default': '1024x1024', 'description': '图像尺寸'},
                    'quality': {'type': 'string', 'default': 'standard', 'description': '图像质量'},
                    'style': {'type': 'string', 'default': 'vivid', 'description': '图像风格'}
                },
                'required': ['prompt']
            }
        )
        
        # GPT图像编辑工具
        tools['create_gpt_image_edit'] = MCPTool(
            name='create_gpt_image_edit',
            description='创建GPT图像编辑任务 - 在给定原始图像和提示的情况下创建编辑或扩展图像',
            parameters={
                'type': 'object',
                'properties': {
                    'image_url': {'type': 'string', 'description': '要编辑的图像URL地址，必须是有效的PNG文件，小于4MB，方形'},
                    'prompt': {'type': 'string', 'description': '所需图像的文本描述，最大长度为1000个字符'},
                    'mask_url': {'type': 'string', 'description': '可选的遮罩图像URL，透明区域指示要编辑的位置'},
                    'n': {'type': 'string', 'default': '1', 'description': '要生成的图像数，必须介于1和10之间'},
                    'size': {'type': 'string', 'default': '1024x1024', 'description': '生成图像的大小，必须是256x256、512x512或1024x1024之一'},
                    'response_format': {'type': 'string', 'default': 'url', 'description': '生成的图像返回格式，必须是url或b64_json'}
                },
                'required': ['image_url', 'prompt']
            }
        )
        
        # Recraft图像生成工具
        tools['create_recraft_image'] = MCPTool(
            name='create_recraft_image',
            description='创建Recraft图像生成任务 - 专业的图像创作工具',
            parameters={
                'type': 'object',
                'properties': {
                    'prompt': {'type': 'string', 'description': '图像描述提示词'},
                    'style': {'type': 'string', 'default': 'realistic', 'description': '图像风格'},
                    'size': {'type': 'string', 'default': '1024x1024', 'description': '图像尺寸'},
                    'image_format': {'type': 'string', 'default': 'png', 'description': '图像格式'}
                },
                'required': ['prompt']
            }
        )
        
        # 即梦3.0图像生成工具
        tools['create_seedream_image'] = MCPTool(
            name='create_seedream_image',
            description='创建即梦3.0图像生成任务 - 先进的图像生成技术',
            parameters={
                'type': 'object',
                'properties': {
                    'prompt': {'type': 'string', 'description': '图像描述提示词'},
                    'aspect_ratio': {'type': 'string', 'default': '1:1', 'description': '宽高比'},
                    'negative_prompt': {'type': 'string', 'description': '负面提示词（可选）'},
                    'cfg_scale': {'type': 'number', 'default': 7.5, 'description': 'CFG缩放值'},
                    'seed': {'type': 'integer', 'description': '随机种子（可选）'}
                },
                'required': ['prompt']
            }
        )
        
        # 即梦垫图生成工具
        tools['create_seededit_image'] = MCPTool(
            name='create_seededit_image',
            description='创建即梦垫图生成任务 - 基于现有图像的智能编辑',
            parameters={
                'type': 'object',
                'properties': {
                    'image_url': {'type': 'string', 'description': '原始图像URL地址'},
                    'prompt': {'type': 'string', 'description': '编辑提示词'},
                    'strength': {'type': 'number', 'default': 0.8, 'description': '编辑强度'},
                    'seed': {'type': 'integer', 'description': '随机种子（可选）'}
                },
                'required': ['image_url', 'prompt']
            }
        )
        
        # FLUX图像生成工具
        tools['create_flux_image'] = MCPTool(
            name='create_flux_image',
            description='创建FLUX图像生成任务 - 高质量的开源图像生成模型',
            parameters={
                'type': 'object',
                'properties': {
                    'prompt': {'type': 'string', 'description': '图像描述提示词'},
                    'aspect_ratio': {'type': 'string', 'default': '1:1', 'description': '宽高比'},
                    'steps': {'type': 'integer', 'default': 20, 'description': '推理步数'},
                    'guidance': {'type': 'number', 'default': 7.5, 'description': '引导强度'},
                    'seed': {'type': 'integer', 'description': '随机种子（可选）'}
                },
                'required': ['prompt']
            }
        )
        
        # StableDiffusion图像生成工具
        tools['create_stable_diffusion_image'] = MCPTool(
            name='create_stable_diffusion_image',
            description='创建StableDiffusion图像生成任务 - 经典的开源图像生成模型',
            parameters={
                'type': 'object',
                'properties': {
                    'prompt': {'type': 'string', 'description': '图像描述提示词'},
                    'size': {'type': 'string', 'default': '1:1', 'description': '图像尺寸比例'},
                    'n': {'type': 'integer', 'default': 1, 'description': '生成图像数量'}
                },
                'required': ['prompt']
            }
        )
        
        # 海螺图片生成工具
        tools['create_hailuo_image'] = MCPTool(
            name='create_hailuo_image',
            description='创建海螺图片生成任务 - 海螺AI的图像生成',
            parameters={
                'type': 'object',
                'properties': {
                    'prompt': {'type': 'string', 'description': '图像描述提示词'},
                    'size': {'type': 'string', 'default': '1024x1024', 'description': '图像尺寸'},
                    'quality': {'type': 'string', 'default': 'standard', 'description': '图像质量'},
                    'seed': {'type': 'integer', 'description': '随机种子（可选）'}
                },
                'required': ['prompt']
            }
        )
        
        # Doubao图片生成工具
        tools['create_doubao_image'] = MCPTool(
            name='create_doubao_image',
            description='创建Doubao图片生成任务 - 字节跳动的图像生成',
            parameters={
                'type': 'object',
                'properties': {
                    'prompt': {'type': 'string', 'description': '图像描述提示词'},
                    'size': {'type': 'string', 'default': '1024x1024', 'description': '图像尺寸'},
                    'guidance_scale': {'type': 'integer', 'default': 3, 'description': '指导强度'},
                    'watermark': {'type': 'boolean', 'default': True, 'description': '是否添加水印'}
                },
                'required': ['prompt']
            }
        )
        
        # 图片上传工具（虚构接口，返回使用指导）
        tools['upload_image_file'] = MCPTool(
            name='upload_image_file',
            description='上传图片文件工具 - 提供图片上传API的使用指导',
            parameters={
                'type': 'object',
                'properties': {
                    'file_description': {'type': 'string', 'description': '图片文件描述（用于提示）'},
                    'folder': {'type': 'string', 'default': 'uploads', 'description': '存储文件夹名称'}
                },
                'required': ['file_description']
            }
        )
        
        return tools
    
    async def handle_mcp_request(self, request: Request) -> Response:
        """处理MCP协议请求"""
        try:
            data = await request.json()
            method = data.get('method')
            request_id = data.get('id')
            params = data.get('params', {})
            
            logger.info(f"MCP request: {method} with id: {request_id}")
            
            if method == 'initialize':
                response = await self._handle_initialize(request_id, params)
            elif method == 'tools/list':
                response = await self._handle_list_tools(request_id)
            elif method == 'tools/call':
                response = await self._handle_call_tool(request_id, params)
            elif method == 'resources/list':
                response = await self._handle_list_resources(request_id)
            elif method == 'resources/read':
                response = await self._handle_read_resource(request_id, params)
            elif method == 'prompts/list':
                response = await self._handle_list_prompts(request_id)
            elif method == 'prompts/get':
                response = await self._handle_get_prompt(request_id, params)
            else:
                response = {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'error': {
                        'code': -32601,
                        'message': f'Method not found: {method}'
                    }
                }
            
            return web.json_response(response)
            
        except Exception as e:
            logger.error(f"Error handling MCP request: {e}")
            return web.json_response({
                'jsonrpc': '2.0',
                'id': data.get('id') if 'data' in locals() else None,
                'error': {
                    'code': -32603,
                    'message': f'Internal error: {str(e)}'
                }
            }, status=500)
    
    async def _handle_initialize(self, request_id: str, params: Dict) -> Dict:
        """处理初始化请求"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'created_at': datetime.now().isoformat(),
            'client_info': params.get('clientInfo', {}),
            'capabilities': params.get('capabilities', {})
        }
        
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': {
                'protocolVersion': '2024-11-05',
                'serverInfo': {
                    'name': 'Images API MCP Service',
                    'version': '1.0.0'
                },
                'capabilities': {
                    'tools': {
                        'listChanged': True
                    },
                    'resources': {
                        'subscribe': False,
                        'listChanged': False
                    },
                    'prompts': {
                        'listChanged': False
                    }
                },
                'sessionId': session_id
            }
        }
    
    async def _handle_list_tools(self, request_id: str) -> Dict:
        """处理工具列表请求"""
        tools_list = []
        for tool in self.tools.values():
            tools_list.append({
                'name': tool.name,
                'description': tool.description,
                'inputSchema': tool.parameters
            })
        
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': {
                'tools': tools_list
            }
        }
    
    async def _handle_call_tool(self, request_id: str, params: Dict) -> Dict:
        """处理工具调用请求"""
        tool_name = params.get('name')
        arguments = params.get('arguments', {})
        
        if tool_name not in self.tools:
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'error': {
                    'code': -32602,
                    'message': f'Unknown tool: {tool_name}'
                }
            }
        
        try:
            # 调用对应的工具函数
            result = await self._execute_tool(tool_name, arguments)
            
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': {
                    'content': [
                        {
                            'type': 'text',
                            'text': result
                        }
                    ],
                    'isError': False
                }
            }
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': {
                    'content': [
                        {
                            'type': 'text',
                            'text': json.dumps({
                                'error': True,
                                'message': str(e),
                                'tool': tool_name
                            }, ensure_ascii=False, indent=2)
                        }
                    ],
                    'isError': True
                }
            }
    
    async def _handle_list_resources(self, request_id: str) -> Dict:
        """处理资源列表请求"""
        resources = getattr(self, 'resources', {})
        resource_list = []
        
        for uri, resource in resources.items():
            resource_list.append({
                'uri': uri,
                'name': resource.get('name', ''),
                'description': resource.get('description', ''),
                'mimeType': 'application/json'
            })
        
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': {
                'resources': resource_list
            }
        }
    
    async def _handle_read_resource(self, request_id: str, params: Dict) -> Dict:
        """处理读取资源请求"""
        uri = params.get('uri')
        
        try:
            content = await self.get_resource(uri)
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': {
                    'contents': [
                        {
                            'uri': uri,
                            'mimeType': 'application/json',
                            'text': json.dumps(content, ensure_ascii=False, indent=2)
                        }
                    ]
                }
            }
        except Exception as e:
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'error': {
                    'code': -32602,
                    'message': f'Resource not found: {uri}'
                }
            }
    
    async def _handle_list_prompts(self, request_id: str) -> Dict:
        """处理提示列表请求"""
        prompts = getattr(self, 'prompts', {})
        prompt_list = []
        
        for name, prompt in prompts.items():
            prompt_list.append({
                'name': name,
                'description': prompt.get('description', ''),
                'arguments': []
            })
        
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': {
                'prompts': prompt_list
            }
        }
    
    async def _handle_get_prompt(self, request_id: str, params: Dict) -> Dict:
        """处理获取提示请求"""
        name = params.get('name')
        
        try:
            content = await self.get_prompt(name)
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': {
                    'description': f"Prompt: {name}",
                    'messages': [
                        {
                            'role': 'user',
                            'content': {
                                'type': 'text',
                                'text': content
                            }
                        }
                    ]
                }
            }
        except Exception as e:
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'error': {
                    'code': -32602,
                    'message': f'Prompt not found: {name}'
                }
            }
    
    async def _execute_tool(self, tool_name: str, arguments: Dict) -> str:
        """执行工具函数"""
        if hasattr(self, '_tool_functions') and tool_name in self._tool_functions:
            func = self._tool_functions[tool_name]
            return await func(**arguments)
        else:
            raise ValueError(f"Tool function not implemented: {tool_name}")
    
    async def get_resource(self, resource_uri: str) -> dict:
        """获取资源内容 - 子类应该重写此方法"""
        return {}
    
    async def get_prompt(self, prompt_name: str) -> str:
        """获取提示内容 - 子类应该重写此方法"""
        return ""
    
    async def health_check(self, request: Request) -> Response:
        """健康检查端点"""
        return web.json_response({
            'status': 'healthy',
            'service': 'Images API MCP Service',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat(),
            'tools_count': len(self.tools),
            'sessions_count': len(self.sessions),
            'python_version': '3.9+',
            'protocol_version': '2024-11-05'
        })
    
    async def service_info(self, request: Request) -> Response:
        """服务信息端点"""
        tools_list = []
        for tool in self.tools.values():
            tools_list.append({
                'name': tool.name,
                'description': tool.description,
                'parameters': tool.parameters
            })
        
        resources_list = []
        if hasattr(self, 'resources'):
            for uri, resource in self.resources.items():
                resources_list.append({
                    'uri': uri,
                    'name': resource.get('name', ''),
                    'description': resource.get('description', '')
                })
        
        prompts_list = []
        if hasattr(self, 'prompts'):
            for name, prompt in self.prompts.items():
                prompts_list.append({
                    'name': name,
                    'description': prompt.get('description', '')
                })
        
        return web.json_response({
            'service': 'Images API MCP Service',
            'version': '1.0.0',
            'protocol_version': '2024-11-05',
            'python_version': '3.9+',
            'transport': 'streamable-http (simplified)',
            'endpoints': {
                'mcp': '/mcp/v1',
                'health': '/mcp/v1/health',
                'tools': '/mcp/v1/tools',
                'info': '/mcp/v1/info'
            },
            'capabilities': {
                'tools': len(tools_list),
                'resources': len(resources_list),
                'prompts': len(prompts_list),
                'sessions': len(self.sessions)
            },
            'tools': tools_list,
            'resources': resources_list,
            'prompts': prompts_list
        })
    
    async def list_tools_http(self, request: Request) -> Response:
        """HTTP方式列出工具"""
        tools_list = []
        for tool in self.tools.values():
            tools_list.append({
                'name': tool.name,
                'description': tool.description,
                'parameters': tool.parameters
            })
        
        return web.json_response({
            'tools': tools_list,
            'count': len(tools_list)
        })

# =============================================================================
# Server Main Function
# =============================================================================

async def create_mcp_server() -> SimpleMCPServer:
    """创建MCP服务器实例"""
    return SimpleMCPServer()

async def run_simple_mcp_server(server_instance: SimpleMCPServer, host: str = '0.0.0.0', port: int = 5513):
    """运行指定的MCP服务器实例"""
    logger.info(f"Starting MCP Server on {host}:{port}")
    
    # 启动服务器
    runner = web.AppRunner(server_instance.app)
    await runner.setup()
    
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    logger.info(f"✅ MCP Server started successfully")
    logger.info(f"📡 MCP Protocol: http://{host}:{port}/mcp/v1")
    logger.info(f"🏥 Health Check: http://{host}:{port}/mcp/v1/health")
    logger.info(f"🛠️ Tools List: http://{host}:{port}/mcp/v1/tools")
    logger.info(f"ℹ️ Service Info: http://{host}:{port}/mcp/v1/info")
    
    # 保持服务运行
    try:
        while True:
            await asyncio.sleep(3600)  # 每小时检查一次
    except KeyboardInterrupt:
        logger.info("Shutting down MCP server...")
        await runner.cleanup()

async def run_mcp_server(host: str = '0.0.0.0', port: int = 5513):
    """运行默认的MCP服务器（向后兼容）"""
    logger.info(f"Starting Simple MCP Server on {host}:{port}")
    
    server = await create_mcp_server()
    await run_simple_mcp_server(server, host, port)

if __name__ == "__main__":
    asyncio.run(run_mcp_server()) 