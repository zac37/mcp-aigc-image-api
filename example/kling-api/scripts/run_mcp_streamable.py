#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Kling API FastMCP 服务器运行脚本 - 使用streamable-http传输
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 强制设置环境变量
os.environ['MCP_TRANSPORT'] = 'streamable-http'

# 导入配置
from core.config import settings

def main():
    """启动FastMCP服务器 - streamable-http模式"""
    # 导入MCP对象
    from routers.mcp.main import app as mcp
    
    # 使用统一配置，但覆盖传输方式
    port = settings.mcp.port
    host = settings.mcp.host
    transport = "streamable-http"  # 强制使用streamable-http
    
    print(f"正在启动FastMCP服务器 - Kling API...")
    print(f"服务端口: {host}:{port}")
    print(f"传输方式: {transport}")
    print("=" * 60)
    
    try:
        # 检查FastMCP版本
        from fastmcp import __version__ as fastmcp_version
        print(f"FastMCP版本: {fastmcp_version}")
        
        # 启动服务器
        print(f"\n启动参数:")
        print(f"  transport: {transport}")
        print(f"  host: {host}")
        print(f"  port: {port}")
        print("\n📌 注意：MCP的streamable-http实际上是POST+SSE混合协议")
        print("  - 发送: POST请求，Content-Type: application/json")
        print("  - 接收: SSE响应，Accept: application/json, text/event-stream")
        print(f"  - 端点: http://{host}:{port}/mcp/v1")
        print("=" * 60)
        
        # 使用streamable-http传输 - 使用命名参数
        mcp.run(transport=transport, host=host, port=port)
                
    except Exception as e:
        print(f"启动FastMCP服务器时出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()